import cv2
import tkinter as tk
from tkinter import filedialog

def choose_video(initial_dir="data/videos"):
    """Open file dialog to pick a video file."""
    root = tk.Tk(); root.withdraw()
    video_path = filedialog.askopenfilename(
        title="Select HOMOGRAPHY video",
        initialdir=initial_dir,
        filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov"), ("All files", "*.*")]
    )
    root.destroy()
    if not video_path:
        raise RuntimeError("No video selected.")
    return video_path

def pick_points(img, min_points=4):
    """Let user click points on an image using OpenCV."""
    pts = []
    disp = img.copy()

    def redraw():
        nonlocal disp
        disp = img.copy()
        h, w = disp.shape[:2]

        instructions = [
            "Click each corner of the calibration board,",
            "starting with the top-left, moving clockwise"
        ]
        for i, line in enumerate(instructions):
            y_pos = 25 + (i * 25)
            cv2.putText(disp, line, (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(disp, line, (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

        msg = "u=Undo   Esc=Exit   Enter=Save"
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2, cv2.LINE_AA)
        cv2.putText(disp, msg, (6, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

        for i, (x, y) in enumerate(pts, 1):
            cv2.circle(disp, (x, y), 4, (0,0,0), 2)
            cv2.circle(disp, (x, y), 3, (255,255,255), -1)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0,0,0), 2, cv2.LINE_AA)
            cv2.putText(disp, str(i), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255,255,255), 1, cv2.LINE_AA)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            pts.append((x, y))
            redraw()

    redraw()
    cv2.namedWindow("Select board corners", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Select board corners", 1000, 700)
    cv2.imshow("Select board corners", disp)
    cv2.setMouseCallback("Select board corners", on_mouse)

    while True:
        cv2.imshow("Select board corners", disp)
        k = cv2.waitKey(1) & 0xFF
        if k in (13, 10) and len(pts) >= min_points:  
            break
        elif k == 27:  # Esc
            pts = []
            break
        elif k in (ord('u'), ord('U')) and pts:
            pts.pop()
            redraw()

    cv2.destroyAllWindows()
    return pts

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

def select_reference_point(frame):
    wheel = {"x": None, "y": None, "set": False}

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            wheel["x"], wheel["y"], wheel["set"] = x, y, True

    win_title = "Click reference point (ESC to cancel)"
    cv2.namedWindow(win_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_title, 900, 600)
    cv2.imshow(win_title, frame)
    cv2.setMouseCallback(win_title, on_mouse)
    while True:
        k = cv2.waitKey(10) & 0xFF
        if wheel["set"] or k == 27:  
            break
    cv2.destroyAllWindows()
    if not wheel["set"]:
        raise RuntimeError("Wheel point not selected (ESC pressed).")
    return wheel["x"], wheel["y"]
