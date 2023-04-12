#!/bin/bash

# Define directories
WORKING_DIR="$HOME/.local/share/botwminstaller"
INSTALLER_DIR="$WORKING_DIR/installer"
MINICONDA_DIR="$WORKING_DIR/miniconda"

# Create necessary directories
mkdir -p "$WORKING_DIR"
mkdir -p "$INSTALLER_DIR"
#mkdir -p "$MINICONDA_DIR"


curl -sL "https://api.github.com/repos/L1Z3/BOTW-Multiplayer-Steam-Deck/tags" \
  | jq -r '.[0].zipball_url' \
  | xargs -I {} curl -sL {} -o "$WORKING_DIR/latest_release.zip"


# Create a temporary directory for extracting the contents of the ZIP file
TEMP_DIR=$(mktemp -d)

# Extract the contents to the temporary directory
unzip "$WORKING_DIR/latest_release.zip" -d "$TEMP_DIR"

# Move the contents of the extracted folder to the installer directory
mv "$TEMP_DIR"/*/* "$INSTALLER_DIR"

# Remove the ZIP file and the temporary directory
rm "$WORKING_DIR/latest_release.zip"
rm -r "$TEMP_DIR"

# Remove the ZIP file
rm "$WORKING_DIR/latest_release.zip"

# Download Miniconda 3.10 portable version
MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-py310_23.1.0-1-Linux-x86_64.sh"
curl -L "$MINICONDA_URL" -o "$WORKING_DIR/miniconda.sh"

# Install Miniconda to the miniconda directory
bash "$WORKING_DIR/miniconda.sh" -b -p "$MINICONDA_DIR" -u

# Activate Miniconda environment
source "$MINICONDA_DIR/bin/activate"

# Install the requirements from the requirements.txt file
pip install -r "$INSTALLER_DIR/requirements.txt"

cd "$INSTALLER_DIR"

# Run the main.py script
python "$INSTALLER_DIR/main.py"

# Deactivate Miniconda environment
conda deactivate
