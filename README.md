This repository contains the source code, calibration tools, and supporting resources accompanying the paper:

**Aitken B., Hu X., Arkell T., Downey L.A., Manning B., Amiguet T., Hayes S., & Hayley A.**

*A validated open-source framework for measuring standard deviation of lateral position during on-road driving.*

---

### Overview

This repository provides an end-to-end, vision-based pipeline to:
- Calibrate camera intrinsic parameters.
- Compute a homography matrix mapping image pixels to real-world road-plane coordinates.
- Measure a vehicle's lateral position relative to a lane line.

Included resources:
- `chessboard_A4.png` — print on **A4** for camera calibration.  
- `calibration_board_B1.png` — print **two copies** on **B1-sized boards** for homography calibration.  
- Cross-platform launchers (`mac_launcher.sh`, `win_launcher.bat`) to automate the entire pipeline.
---

### Quick Start (TL;DR)
1. Print `chessboard_A4.png`, capture 10–15 images, and save them tos `data/chessboard_images/`.
2. Print 2 × `calibration_board_B1.png`, record a 5–10 s video, and save it to `data/videos/`.
3. Record a driving video using the same camera mount and save it to `data/videos/`.
4. Run the launcher (`mac_launcher.sh` or `win_launcher.bat`).
5. Collect outputs from `output/csv/` (for analysis) and `output/videos/` (for visual inspection).

---

### Respository Structure

```
lane-detection/
│
├── chessboard_A4.png               # A4 calibration chessboard
├── calibration_board_B1.png        # B1 calibration board
│
├── data/
│   ├── chessboard_images/          # Chessboard images go here
│   ├── calib/                      # Generated calibration files (.npz)
│   ├── homography/                 # Generates homography files (.json)
│   ├── videos/                     # Your videos go here
│   └── sample_data/                # Sample dataset and output
│       ├── chessboard_images/      
│       │   ├── chessboard1.png
│       │   ├── chessboard2.png
│       │   └── ... (chessboard15.png)
│       ├── videos/             
│       │   ├── homography_sample.mov
│       │   └── driving_sample.mov
│       └── expected_outputs/
│           ├── calib/
│           │   └── camera_instrinsics_sample.npz
│           ├── homography/
│           │   └── homography_sample.json
│           ├── csv/
│           │   └── driving_sample_measurements.csv
│           └── videos/
│               └── driving_sample_debug.mp4
│
├── output/
│   ├── csv/                        # Measurement CSVs (per frame)
│   └── videos/                     # Debug videos
│
├── src/
│   ├── calibration.py              # Calculates camera intrinsic from chessboard images
│   ├── config.py                   # Loads config.json including wheel offset and detection parameters
│   ├── homography.py               # Compute/validate/save 3×3 homography mapping (image → road plane)
│   ├── measurement.py              # Pixel → world coordinate mapping + distance calculations
│   └── utils.py                    # Misc. shared helpers (paths, dialogs, overlays)
│
├── scripts/
│   ├── run_calibration.py          # Intrinsic calibration
│   ├── run_homography.py           # Homography matrix generation
│   └── run_measurement.py          # Lane measurement
│
│── launchers/
│   ├── mac_launcher.sh             # macOS/Linux launcher
│   └── win_launcher.bat            # Windows launcher
│ 
├── requirements.txt                # Python dependencies
└── README.md                       # This document
```

---

### Installation

#### 1. Get the code
**Option A: Clone with Git**
```bash
git clone https://github.com/blair-aitken/lane_detection.git
cd lane_detection
```

**Option B: Download ZIP**
1. Download the latest release [here](https://github.com/blair-aitken/lane-detection/archive/refs/heads/main.zip)
2. Extract the downloaded ZIP file
3. Navigate to the extracted folder in your terminal (macOS/Linux) or Command Prompt (Windows)

#### 2. Install Python

If you don't have Python 3.9+ installed, follow these instructions.

#### For macOS:
- Install Homebrew (package manager for macOS) if you don’t already have it:
 
 ```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- Install Python:

```bash
brew install python
```

- Verify installation:

```bash
python3 --version
pip3 --version
```

#### For Windows:
- Go to [python.org](https://www.python.org/downloads/windows/) and download the latest stable release (Python 3.9+).
- Run the installer
  - During installation, check the box that says `Add Python to PATH`.
  - Choose “Install Now.”
- Verify installation:

```bat
python --version
pip --version
```

---

### Data Preparation

Before measuring lane position, complete two short calibration steps:

- Capture chessboard images for camera intrinsics.
- Record a homography video to map image pixels to road-plane coordinates.

#### Chessboard Images

We use a printed chessboard pattern to estimate intrinsic camera parameters and correct lens distortion, ensuring geometrically accurate measurements from the video.

1. Print `chessboard_A4.png` on A4 paper.
2. Mount flat on stiff cardboard or foam board (no bending).
3. Capture 10–15 images with your camera, varying position, angle, and distance.

<img alt="chessboard_image" src="https://github.com/user-attachments/assets/83a2da6d-1dc9-4dcf-bdd1-991a540db387" width="500">

4. Save all images into `data/chessboard_images/`

#### Homography Video

We use calibration boards on the road to generate a homography, allowing the software to learn how your camera projects distances onto the image.

1. Print two copies of `calibration_board_B1.png` on **B1-sized boards.**
2. Park your car on a flat road or the same test track you’ll use for driving.
3. Place both boards flat on the ground beside the measured wheel, with the short edge against the tyre (or other vehicle reference point).

 <img alt="homography_calibration" src="https://github.com/user-attachments/assets/9cc1c110-10b1-45b9-907c-b0a95fb12942" width="500">

4. Record a 5–10 s video (**.mkv**, **.mp4**, **.avi**, **.mov**) using the final camera mount.
5. Save the video into `data/videos/`

#### Record Your Driving Video

This is the video the system will analyse for lane position. It must be recorded with the same camera mount used for calibration and homography.

1. Mount the camera securely above the wheel so the lane line is clearly visible.
2. Record your driving video (**.mkv**, **.mp4**, **.avi**, **.mov**).
3. Save it into `data/videos/`
  
---

### Configuration

A `config.json` file is created in the repository root the first time you run a launcher. This file stores key parameters, including detection settings and the wheel-to-centre offset.

The most important paramter is `wheel_offset_cm`, which accounts for vehicle width:

- Measure the total width of your vehicle (outer wheel to outer wheel) and divide by 2.
- Enter this value using the same units you will use for analysis (for example, centimetres).
- This is used to convert wheel-to-lane distance into vehicle-centre-to-lane distance.

Most users can leave the remaining settings at their defaults unless fine-tuning detection for specific cameras, road types, or lighting conditions.

| Variable | Description | Current Value |
| --- | --- |--- |
| WHEEL_OFFSET_CM | Constant offset added to the computed wheel → lane distance | User defined |
| GAUSSIAN_KERNEL | Gaussian blur kernel applied to grayscale image (noise suppression; must be odd×odd) | (15, 15) |
| LOCAL_WINDOW | Kernel for local mean (cv2.blur) used in the reflectance gate (bigger = smoother local illumination estimate) | (45, 45) |
| REFLECTANCE_DELTA | Reflectance gate threshold: keeps pixels where blurred > local_mean + delta (higher = stricter, fewer pixels pass) | 10 |
| ADAPTIVE_BLOCK_SIZE | Adaptive threshold window size (odd, ≥3). Larger adapts to broader lighting gradients but can wash out fine detail | 61 |
| ADAPTIVE_C | Constant subtracted in adaptive thresholding (more negative = stricter; fewer white pixels) | -8 |
| MIN_CONTOUR_AREA | Rejects connected components smaller than this (px²) before shape filtering | 12500 |
| MIN_ASPECT_RATIO | Shape filter using bounding box ratio max(w,h)/min(w,h); keeps long/thin blobs (lane-like) | 6 |
| MIN_FILL_RATIO | Fill ratio filter: area/(w*h); rejects hollow/fragmented blobs even if long/thin | 0.2 |
| CLOSE_KERNEL | Morphological close kernel (fills small gaps, connects broken paint segments) | (35, 3) |
| OPEN_KERNEL | Morphological open kernel (removes small specks / noise after closing) | (5, 5) |
| COLUMN_HALF_WIDTH | Half-width (px) of the vertical strip sampled around wheel_x for lane localisation | 7 |
| VERTICAL_EXCLUSION_PX | Excludes a band immediately above the wheel reference point when extracting the vertical search strip to avoid wheel edge interfering with lane detection | 10 |
| OPEN_KERNEL | Morphological open kernel (removes small specks / noise after closing) | (5, 5) |
| COLUMN_HALF_WIDTH | Half-width (px) of the vertical strip sampled around wheel_x for lane localisation | 7 |

---

### How It Works

Use the launcher script for your operating system.

**macOS / Linux**  

Open a terminal in the project folder, make the launcher executable (first time only), then run:

```bash
cd launchers
chmod +x mac_launcher.sh
./mac_launcher.sh
```

**Windows**

Simply double-click win_launcher.bat in File Explorer,
or run it from Command Prompt / PowerShell:
```bat
launchers/win_launcher.bat
```

When you run the launcher, the following steps will run in sequence:

#### Step 0: Pre-flight Checks
- **System Requirements**: Verifies Python 3.9+ is installed and available.
- **Configuration Setup**: Creates `config.json` if it doesn't exist, or loads existing settings.
- **Vehicle Configuration**: Prompts you to configure the critical `wheel_offset_cm` parameter.
  - Shows your previously saved value if one exists.
  - Allows you to keep the existing value or enter a new one.
  - Provides clear instructions on how to measure this value for your specific vehicle.
  - This step ensures accurate conversion from wheel-to-lane measurements to centre-of-vehicle-to-lane measurements.

#### Step 1: Virtual Environment Setup
- The first time you run the project, it will create a folder called `venv/`
- This folder contains a self-contained Python installation just for this project.
- All the project’s dependencies will be installed into venv/, instead of into your system Python.

#### Step 2: Verify Tkinter Support
- **Tkinter Verification**: Ensures Python installation includes Tkinter GUI support, which is required for:
  - Camera calibration interface
  - Homography point selection GUI
  - Interactive measurement confirmation
- Searches for Python installations with working Tkinter in this order:
  - **macOS**: Homebrew Python → pyenv → version-specific → system Python
  - **Windows**: Standard Python → Python Launcher → common installation paths
- If missing, clear installation instructions are provided to guide the user in enabling Tkinter support.

#### Step 3: Install Dependencies
- All required dependencies listed in `requirements.txt` are installed into the virtual environment.  

#### Step 4: Camera Calibration
- Run camera calibration using the printed chessboard pattern.
- **Input:** at least 10 chessboard images from `data/chessboard_images` (`*.jpg`, `*.jpeg`, `*.png`, `*.bmp`, `*.tif`, `*.tiff`).
- **Output:**
  - `data/calib/camera_intrinsics.npz` (camera matrix and distortion coefficients).
  - `camera_intrinsics_summary.json` (summary of calibration, RMS error, number of images).

<img alt="calibrate_camera_intrinsics" src="https://github.com/user-attachments/assets/c9a9548f-ee36-4a5c-9cbc-680f9d08b17d" width="500"><br>

#### Step 5: Compute Homography Matrix
- Run homography generation using the calibration board.
- **Input:** short calibration-board video from data/videos/.
- You will be prompted to click the four board corners (top-left first, then clockwise).
- A 3×3 homography matrix is computed and saved as `data/homography/[video_name]_homography.json`
- **Optional sanity check:** select two points on the board to verify that distances in the transformed space match the known board dimensions (for example, square height and width in cm).

#### Step 6: Lane Measurement
- With calibration and homography set, you can now measure lane position from a driving video.  
- **Input:** Wheel-view driving video.
- You’ll be prompted to click on the wheel reference point once.  
- For each frame:
  - Lane line is detected using a histogram-based method.  
  - Distance between the wheel and lane line is mapped to real-world coordinates.
 
---

### Main Outputs (from your driving video)

After calibration and homography are set, running the pipeline on your driving video produces two main outputs:

- **CSV file** (`output/csv/[video_name]_measurements.csv`):  
  - Contains frame-by-frame measurements of the vehicle’s lateral position.  
  - Values represent the distance from wheel → lane line, corrected by the wheel-to-vehicle centre offset.  
  - `NaN` indicates no valid lane line was detected for that frame.  

- **Debug video** (`output/videos/[video_name]_debug.mp4`):  
  - Shows the wheel reference point, detected lane line, frame number, and lateral distance.  
  - Frame numbers in the video **match the rows in the CSV**.  
  - Useful for:  
    - Visually inspect detection quality.  
    - Identifying errors (e.g., shadows, passing vehicles).  
    - Manually cleaning the CSV before final analysis.  

At the end of processing, the script also prints **summary statistics** in the terminal.

<img alt="summary_statistics" src="https://github.com/user-attachments/assets/63aeb140-9ba3-480e-bb11-4f0b0823e1a9" width="500">

---

### Sample Data
A small example dataset is included in `data/sample_data/` so you can test the full pipeline without collecting your own data first.

---

### Limitations

This toolkit is designed for controlled experiments and may not perform perfectly in all conditions. Key limitations to be aware of:
- Lighting and shadows
  - Lane detection works best with clearly visible white or yellow lines.
  - Strong shadows, glare, or faded markings can reduce accuracy.
- Board calibration
  - Camera calibration requires sharp, in-focus chessboard images. Blurry or warped boards will degrade results.
  - Homography calibration must be done with the same camera mount used for the driving video. Any change in angle or height requires recalibration.
- Vehicle-specific setup
  - The only configuration parameter that must be changed per vehicle is wheel_offset_cm. An incorrect value will shift the lane-centre measurements.
- Data quality
  - The system assumes stable camera mounting. Vibrations or loose mounts can distort results.
  - NaN values in the CSV indicate frames where no reliable lane line was detected. Manual cleaning of the CSV may be required for final analysis.

---

### Troubleshooting

- **`No calibration file found`**  
  → Run the calibration step again with `chessboard.png`.  

- **`No homography file exists`**  
  → Run homography generation with the calibration boards.  

- **`Wheel point mis-clicked`**  
  → Rerun measurement and click the correct wheel reference point.  

- **`Permission denied (macOS/Linux)`**  
  → Make the launcher executable:  
  ```bash
  chmod +x mac_launcher.sh
  ```
- **`GUI requirements`**  
  → This project uses Tkinter for file selection dialogs.
    - Tkinter is included with standard Python distributions on Windows, macOS, and Linux.
    - If you see an error like `ModuleNotFoundError: No module named '_tkinter'`, make sure your Python installation includes Tk support:
    - **macOS**
      - **Install via Homebrew (recommended)**:
        ```bash
        brew install python
        ```
      - **Install via pyenv**:
        ```bash
        brew install pyenv && pyenv install 3.11.5
        ```
      - **Avoid system Python**: macOS system Python often has broken Tkinter
      - **Windows**
    - **Windows**:
      - **Reinstall from [python.org](https://www.python.org/downloads/windows/)**: Download the official installer and ensure "tcl/tk and IDLE" is selected
      - **Check PATH**: Make sure "Add Python to PATH" was selected during installation
      - **Conda users**: conda install tk if using Anaconda/Miniconda

---

## Validation dataset

The validation dataset used in the accompanying manuscript is available separately on Zenodo:

**DOI:** https://doi.org/10.5281/zenodo.21798890

The dataset includes:

- Raw camera images

- Camera calibration files

- Homography parameters

- Binary lane masks

- Debug images with detected lane boundaries and lateral position estimates

- Frame-level measurement data

---

### License
This project is open source and available under the [MIT License](LICENSE).
