#!/bin/bash

# Define directories
WORKING_DIR="$HOME/.local/share/botwminstaller"
INSTALLER_DIR="$WORKING_DIR/installer"
MINICONDA_DIR="$WORKING_DIR/miniconda"
VERSION_FILE="$WORKING_DIR/version.txt"

# Create necessary directories
mkdir -p "$WORKING_DIR"
mkdir -p "$INSTALLER_DIR"

# Get the latest release information from GitHub API
LATEST_RELEASE_INFO=$(curl -sL "https://api.github.com/repos/L1Z3/BOTW-Multiplayer-Steam-Deck/tags")

# Extract the tag name (version) and zipball URL of the latest release
LATEST_VERSION=$(echo "$LATEST_RELEASE_INFO" | jq -r '.[0].name')
ZIPBALL_URL=$(echo "$LATEST_RELEASE_INFO" | jq -r '.[0].zipball_url')

# Check if the version file exists and read its content
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE")
else
    CURRENT_VERSION=""
fi

# Compare the current version with the latest version and proceed with download if necessary
if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    # Update the version file with the latest version
    echo "$LATEST_VERSION" > "$VERSION_FILE"

    # Download the latest release
    curl -sL "$ZIPBALL_URL" -o "$WORKING_DIR/latest_release.zip"

    # Create a temporary directory for extracting the contents of the ZIP file
    TEMP_DIR=$(mktemp -d)

    # Extract the contents to the temporary directory
    unzip "$WORKING_DIR/latest_release.zip" -d "$TEMP_DIR"

    # Remove the previous unzipped installer using find command
    find "$INSTALLER_DIR" -mindepth 1 -delete

    # Move the contents of the extracted folder to the installer directory
    mv "$TEMP_DIR"/*/* "$INSTALLER_DIR"

    # Remove the ZIP file and the temporary directory
    rm "$WORKING_DIR/latest_release.zip"
    rm -r "$TEMP_DIR"

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
fi
