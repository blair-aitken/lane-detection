import cv2, json, os, sys
import numpy as np
import tkinter as tk
from tkinter import filedialog
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.utils import find_calibration_file
from src.homography import compute_homography, save_homography, pixel_to_real_world
from src.ui_helpers import choose_video, pick_points

def main():
    calib_path = find_calibration_file()
    calib = np.load(calib_path)
    camera_matrix, dist_coeffs = calib["camera_matrix"], calib["dist_coeffs"]

    video_path = choose_video()
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    out_json = os.path.join("data", "homography", f"{base_name}_homography.json")

    if os.path.exists(out_json):
        print(f"[homography] Overwriting existing file → {out_json}")

    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read first frame from {video_path}")

    undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
    pts = pick_points(undistorted, min_points=4)
    if len(pts) < 4:
        print("[homography] Cancelled (not enough points).")
        return None

    real_pts = [(0, 0), (70, 0), (70, 200), (0, 200)]
    H = compute_homography(pts, real_pts)

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    save_homography(H, out_json)
    print(f"[homography] saved → {os.path.abspath(out_json)}")

    check_frame = undistorted.copy()
    points = []

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 2:
                points.append((x, y))

    cv2.namedWindow("Homography Check")
    cv2.setMouseCallback("Homography Check", on_click)

    while True:
        disp = check_frame.copy()
        h, w = disp.shape[:2]

        msg = "Enter=Confirm   r=Reset   Esc=Exit"
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2, cv2.LINE_AA)
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

        for i, (x, y) in enumerate(points, 1):
            cv2.circle(disp, (x, y), 4, (0,0,0), 2)
            cv2.circle(disp, (x, y), 3, (255,255,255), -1)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255,255,255), 1, cv2.LINE_AA)

        if len(points) == 2:
            rw_pts = [pixel_to_real_world(pt, H) for pt in points]
            dist = np.sqrt((rw_pts[0][0] - rw_pts[1][0])**2 +
                           (rw_pts[0][1] - rw_pts[1][1])**2)
            text = f"Distance: {dist:.2f} cm"
            cv2.putText(disp, text,
                        (w - 200, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(disp, text,
                        (w - 200, h - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow("Homography Check", disp)
        key = cv2.waitKey(20) & 0xFF

        if key == 27:   # ESC
            break
        elif key in (ord('r'), ord('R')):
            points = []
        elif key in (13, 10):  # Enter
            break

    cv2.destroyWindow("Homography Check")
    return out_json


if __name__ == "__main__":
    main()
