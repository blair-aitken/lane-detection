import numpy as np
import math
from src.config import COLUMN_HALF_WIDTH, VERTICAL_EXCLUSION_PX

def pixel_to_real_world(pixel_point, H):
    pt = np.array([[pixel_point[0], pixel_point[1], 1]], dtype=np.float32).T
    world = np.dot(H, pt)
    if world[2] == 0:
        raise ValueError("Invalid homography transform (division by zero).")
    return (world[0] / world[2])[0], (world[1] / world[2])[0]


def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def find_lane_line_by_histogram(
    binary_img,
    wheel_x,
    wheel_y,
    prev_detection=None,
    column_half_width=None,
    vertical_exclusion_px=None
):
    if column_half_width is None:
        column_half_width = config.COLUMN_HALF_WIDTH
    if vertical_exclusion_px is None:
        vertical_exclusion_px = config.VERTICAL_EXCLUSION_PX

    # Define search region
    x_min = max(0, int(wheel_x - column_half_width))
    x_max = min(binary_img.shape[1], int(wheel_x + column_half_width))
    y_max = max(0, int(wheel_y - vertical_exclusion_px))

    if x_min >= x_max or y_max <= 0:
        return None

    strip = binary_img[0:y_max, x_min:x_max]

    # Get coordinates of lane pixels
    ys, xs = np.where(strip == 255)
    if len(xs) == 0:
        return None

    # Convert to image coordinates
    xs = xs + x_min
    ys = ys

    # Compute distance to wheel point
    dx = xs - wheel_x
    dy = ys - wheel_y
    dists = np.sqrt(dx**2 + dy**2)

    # Optional temporal stabilisation
    if prev_detection is not None:
        px, py = prev_detection
        prev_dist = np.sqrt((xs - px)**2 + (ys - py)**2)
        dists = 0.7 * dists + 0.3 * prev_dist

    idx = np.argmin(dists)
    return (int(xs[idx]), int(ys[idx]))
