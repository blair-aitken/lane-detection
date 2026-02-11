import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config.json")

CALIB_SEARCH_DIR = "data/calib"
HOMOGRAPHY_SEARCH_DIR = "data/homography"

DEFAULT_CONFIG = {

    "gaussian_kernel": [15, 15],
    "adaptive_block_size": 61,
    "adaptive_c": -8,
    "min_contour_area": 12500,
    "min_aspect_ratio": 6.0,
    "min_fill_ratio": 0.20,
    "morph_close_kernel": [35, 3],
    "morph_open_kernel": [5, 5],
    "column_half_width": 7,
    "vertical_exclusion_px": 10,
    "wheel_offset_cm": 0.0
}

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    print(f"[config] created default config.json → {CONFIG_FILE}")

with open(CONFIG_FILE, "r") as f:
    _cfg = json.load(f)

GAUSSIAN_KERNEL = tuple(_cfg.get("gaussian_kernel", DEFAULT_CONFIG["gaussian_kernel"]))
ADAPTIVE_BLOCK_SIZE = _cfg.get("adaptive_block_size", DEFAULT_CONFIG["adaptive_block_size"])
ADAPTIVE_C = _cfg.get("adaptive_c", DEFAULT_CONFIG["adaptive_c"])
MIN_CONTOUR_AREA = _cfg.get("min_contour_area", DEFAULT_CONFIG["min_contour_area"])
MIN_ASPECT_RATIO = _cfg.get("min_aspect_ratio", DEFAULT_CONFIG["min_aspect_ratio"])
MIN_FILL_RATIO   = _cfg.get("min_fill_ratio", DEFAULT_CONFIG["min_fill_ratio"])
MORPH_CLOSE_KERNEL = tuple(_cfg.get("morph_close_kernel", DEFAULT_CONFIG["morph_close_kernel"]))
MORPH_OPEN_KERNEL  = tuple(_cfg.get("morph_open_kernel", DEFAULT_CONFIG["morph_open_kernel"]))
COLUMN_HALF_WIDTH = _cfg.get("column_half_width", DEFAULT_CONFIG["column_half_width"])
VERTICAL_EXCLUSION_PX = _cfg.get("vertical_exclusion_px", DEFAULT_CONFIG["vertical_exclusion_px"])
WHEEL_OFFSET_CM = _cfg.get("wheel_offset_cm", DEFAULT_CONFIG["wheel_offset_cm"])

def ensure_vehicle_config():
    import json
    import os

    print("\nVehicle Configuration")
    print("=" * 58)
    print()
    print("The wheel_offset_cm value is critical for accurate measurements.")
    print("It should be half of your vehicle's wheel-to-wheel track width.")
    print()

    wheel_offset = WHEEL_OFFSET_CM

    if wheel_offset and wheel_offset > 0:
        print(f"Current setting: {wheel_offset:.1f} cm")
    else:
        print("Current setting: Not configured")

    print()
    print("To measure this:")
    print("1. Measure the distance between wheel centers (left to right)")
    print("2. Divide by 2 to get the wheel offset")
    print()

    while True:
        if wheel_offset and wheel_offset > 0:
            resp = input(
                f"Enter wheel offset in cm (press Enter to keep {wheel_offset:.1f}): "
            ).strip()
            if resp == "":
                print(f"\nUsing existing wheel_offset_cm = {wheel_offset:.1f} cm\n")
                return
        else:
            resp = input("Enter wheel offset in cm: ").strip()

        try:
            new_offset = float(resp)
            if new_offset <= 0:
                raise ValueError
        except ValueError:
            print("Please enter a valid positive number.\n")
            continue

        confirm = input(
            f"Use wheel_offset_cm = {new_offset:.1f} cm? (y/n): "
        ).strip().lower()

        if confirm == "y":
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)

            cfg["wheel_offset_cm"] = new_offset

            with open(CONFIG_FILE, "w") as f:
                json.dump(cfg, f, indent=4)

            print(f"\nUpdated wheel_offset_cm to {new_offset:.1f} cm\n")
            return
        else:
            print("Try again.\n")
