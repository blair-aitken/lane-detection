import cv2, os, json, csv, sys
import numpy as np
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.config import (
    GAUSSIAN_KERNEL,
    ADAPTIVE_BLOCK_SIZE,
    ADAPTIVE_C,
    MIN_CONTOUR_AREA,
    MIN_ASPECT_RATIO,
    MIN_FILL_RATIO,
    MORPH_CLOSE_KERNEL,
    MORPH_OPEN_KERNEL,
    COLUMN_HALF_WIDTH,
    VERTICAL_EXCLUSION_PX,
    WHEEL_OFFSET_CM,
)
from src.measurement import (
    pixel_to_real_world,
    calculate_distance,
    find_lane_line_by_histogram
)

def choose_files():
    root = tk.Tk()
    root.withdraw()

    video_path = filedialog.askopenfilename(
        title="Select input VIDEO",
        initialdir="data/videos",
        filetypes=[("Video files", "*.mkv *.mp4 *.avi *.mov"), ("All files", "*.*")]
    )
    if not video_path:
        raise RuntimeError("No video selected.")

    homog_path = filedialog.askopenfilename(
        title="Select HOMOGRAPHY JSON",
        initialdir="data/homography",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not homog_path:
        raise RuntimeError("No homography file selected.")

    root.destroy()
    return video_path, homog_path

def main():
    video_path, homog_path = choose_files()

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    out_csv_path = os.path.join("output", "csv", f"{base_name}_measurements.csv")
    out_video_path = os.path.join("output", "videos", f"{base_name}_debug.mp4")
    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(out_video_path), exist_ok=True)

    calib_path = "data/calib/camera_intrinsics.npz"
    if not os.path.exists(calib_path):
        raise RuntimeError("No calibration found. Run calibration first.")
    calib = np.load(calib_path)
    camera_matrix = calib["camera_matrix"]
    dist_coeffs = calib["dist_coeffs"]

    with open(homog_path, "r") as f:
        data = json.load(f)
    H_list = data.get("homography_matrix") or data.get("H") or data
    homography_matrix = np.array(H_list, dtype=np.float32)
    if homography_matrix.shape != (3, 3):
        raise RuntimeError(f"Homography is not 3x3: {homography_matrix.shape}")

    cap = cv2.VideoCapture(video_path)
    total_frames_meta = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read first frame")

    first_frame = cv2.undistort(first_frame, camera_matrix, dist_coeffs)

    wheel = {"x": None, "y": None, "set": False}

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            wheel["x"], wheel["y"], wheel["set"] = x, y, True

    cv2.imshow("Click reference point (ESC to cancel)", first_frame)
    cv2.setMouseCallback("Click reference point (ESC to cancel)", on_mouse)

    while True:
        if wheel["set"] or (cv2.waitKey(10) & 0xFF) == 27:
            break
    cv2.destroyAllWindows()

    if not wheel["set"]:
        raise RuntimeError("Wheel point not selected.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out_vid = cv2.VideoWriter(
        out_video_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    all_distances = []
    nan_count = 0
    prev_lane_detection = None

    with open(out_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "cm_to_lane"])

        with tqdm(total=total_frames_meta if total_frames_meta > 0 else None, unit="frame") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

                undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
                gray = cv2.cvtColor(undistorted, cv2.COLOR_BGR2GRAY)

                blurred = cv2.GaussianBlur(
                    gray, GAUSSIAN_KERNEL, 0
                )

                adaptive = cv2.adaptiveThreshold(
                    blurred, 255,
                    cv2.ADAPTIVE_THRESH_MEAN_C,
                    cv2.THRESH_BINARY,
                    ADAPTIVE_BLOCK_SIZE,
                    ADAPTIVE_C
                )

                contours, _ = cv2.findContours(
                    adaptive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                clean = np.zeros_like(adaptive)
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    area = w * h
                    aspect = max(w, h) / (min(w, h) + 1e-6)
                    fill = cv2.contourArea(cnt) / (area + 1e-6)

                    if (
                        area >= MIN_CONTOUR_AREA and
                        aspect >= MIN_ASPECT_RATIO and
                        fill >= MIN_FILL_RATIO
                    ):
                        cv2.drawContours(clean, [cnt], -1, 255, -1)

                adaptive = cv2.morphologyEx(
                    clean,
                    cv2.MORPH_CLOSE,
                    cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_CLOSE_KERNEL),
                    iterations=1
                )

                adaptive = cv2.morphologyEx(
                    adaptive,
                    cv2.MORPH_OPEN,
                    cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_OPEN_KERNEL),
                    iterations=1
                )

                pt_lane = find_lane_line_by_histogram(
                    adaptive,
                    wheel["x"],
                    wheel["y"],
                    prev_lane_detection,
                    column_half_width=COLUMN_HALF_WIDTH,
                    vertical_exclusion_px=VERTICAL_EXCLUSION_PX
                )

                if pt_lane is not None:
                    prev_lane_detection = pt_lane

                    real_wheel = pixel_to_real_world(
                        (wheel["x"], wheel["y"]), homography_matrix
                    )
                    real_lane = pixel_to_real_world(
                        pt_lane, homography_matrix
                    )

                    lateral_pos = (
                        calculate_distance(real_wheel, real_lane)
                        + WHEEL_OFFSET_CM
                    )

                    all_distances.append(lateral_pos)
                    writer.writerow([frame_idx, lateral_pos])

                    cv2.line(
                        undistorted,
                        (wheel["x"], wheel["y"]),
                        pt_lane,
                        (255, 255, 255),
                        2
                    )

                    cv2.putText(
                        undistorted,
                        f"{lateral_pos:.1f} cm",
                        (width - 160, height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        1
                    )
                else:
                    nan_count += 1
                    writer.writerow([frame_idx, "NaN"])

                cv2.putText(
                    undistorted,
                    f"Frame {frame_idx}",
                    (10, height - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )

                out_vid.write(undistorted)
                pbar.update(1)

    cap.release()
    out_vid.release()

    print("\n[summary statistics]")
    frames_valid = len(all_distances)
    frames_total = frames_valid + nan_count

    if frames_valid > 0:
        arr = np.array(all_distances)
        print(f"  Valid frames: {frames_valid} / {frames_total} ({frames_valid/frames_total*100:.1f}%)")
        print(f"  NaN frames:   {nan_count} / {frames_total} ({nan_count/frames_total*100:.1f}%)")
        print(f"  Mean:   {np.mean(arr):.2f} cm")
        print(f"  Median: {np.median(arr):.2f} cm")
        print(f"  Min:    {np.min(arr):.2f} cm")
        print(f"  Max:    {np.max(arr):.2f} cm")
        if frames_valid > 1:
            print(f"  SDLP:   {np.std(arr, ddof=1):.2f} cm")
    else:
        print("  No valid lane detections.")

# ======================================================
if __name__ == "__main__":
    main()
