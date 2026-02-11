#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

BOLD=$(tput bold)
RESET=$(tput sgr0)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
CYAN=$(tput setaf 6)
RED=$(tput setaf 1)

divider() {
  echo -e "\n${CYAN}------------------------------------------------------------${RESET}\n"
}

section() {
  divider
  echo -e "${BOLD}$1${RESET}\n"
}

find_python_with_tkinter() {
  local python_candidates=(
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "$HOME/.pyenv/shims/python3"
    "python3.12"
    "python3.11"
    "python3.10"
    "python3.9"
    "python3"
    "/usr/bin/python3"
  )

  for python_cmd in "${python_candidates[@]}"; do
    if command -v "$python_cmd" &> /dev/null; then
      if "$python_cmd" -c "import tkinter" &> /dev/null; then
        PYTHON_CMD="$python_cmd"
        return 0
      fi
    fi
  done
  return 1
}

verify_venv_tkinter() {
  ./venv/bin/python -c "import tkinter" &> /dev/null
}

# -----------------------------------------------------
section "[0/6] Pre-flight Checks"

PYTHON_CMD=""
if ! find_python_with_tkinter; then
  echo "${RED}No Python installation with Tkinter support found.${RESET}"
  echo "Please install Python 3.9+ with Tkinter support and try again."
  exit 1
fi

python_version=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo "${GREEN}Using Python $python_version → $PYTHON_CMD${RESET}"

# -----------------------------------------------------
section "[1/6] Environment Setup"

if [ ! -d "venv" ]; then
  echo "${YELLOW}Creating virtual environment...${RESET}"
  "$PYTHON_CMD" -m venv venv
else
  echo "${GREEN}Virtual environment already exists.${RESET}"
fi

if ! verify_venv_tkinter; then
  printf "\n"
  echo "${YELLOW}Recreating virtual environment with Tkinter support...${RESET}"
  rm -rf venv
  "$PYTHON_CMD" -m venv venv
fi

"$PYTHON_CMD" -c "from src import config; config.ensure_vehicle_config()"

# -----------------------------------------------------
section "[2/6] Verify Tkinter Support"

if verify_venv_tkinter; then
  echo "${GREEN}Tkinter available in virtual environment${RESET}"
else
  echo "${RED}Tkinter not available in virtual environment.${RESET}"
  exit 1
fi

# -----------------------------------------------------
section "[3/6] Install Dependencies"

./venv/bin/python -m pip install --upgrade pip >/dev/null
./venv/bin/python -m pip install -r requirements.txt

# -----------------------------------------------------
section "[4/6] Calibrate Camera Intrinsics"

if [ ! -f "data/calib/camera_intrinsics.npz" ]; then
  echo "${YELLOW}No camera intrinsics found — running calibration...${RESET}"
  printf "\n"
  ./venv/bin/python scripts/run_calibration.py
else
  echo "${GREEN}Using existing camera_intrinsics.npz${RESET}"
fi

# -----------------------------------------------------
section "[5/6] Compute Homography Matrix"

if [ ! -f "data/calib/camera_intrinsics.npz" ]; then
  echo "${RED}Camera intrinsics not found.${RESET}"
  printf "\n"
  exit 1
fi

read -p "Generate a new homography matrix? (y/n): " yn
printf "\n"

if [[ "$yn" =~ ^[Yy]$ ]]; then
  ./venv/bin/python scripts/run_homography.py
else
  printf "\n"
  echo "${GREEN}Skipping homography generation.${RESET}"
  printf "\n"
fi

# -----------------------------------------------------
section "[6/6] Calculate Lateral Position"

./venv/bin/python scripts/run_measurement.py

# -----------------------------------------------------
divider
printf "%sPipeline complete.%s\n\n" "$GREEN" "$RESET"
printf "Outputs:\n"
printf "  • CSV results:   output/csv/\n"
printf "  • Debug videos:  output/videos/\n\n"