#!/bin/bash

################################################################################
# Universal DMG Builder
#
# This script creates consistently styled DMG installers for macOS applications.
# It reads configuration from a dmg-config.json file in your project.
#
# Usage: ./universal-dmg-builder.sh [path/to/dmg-config.json]
#        If no config path provided, looks for ./dmg-config.json
################################################################################

set -e  # Exit on any error

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions for colored output
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

################################################################################
# STEP 1: Load Configuration
################################################################################

CONFIG_FILE="${1:-./dmg-config.json}"

if [ ! -f "$CONFIG_FILE" ]; then
    error "Configuration file not found: $CONFIG_FILE"
fi

info "Loading configuration from $CONFIG_FILE"

# Parse JSON config using Python (available on all macOS systems)
PARSER_SCRIPT=$(mktemp /tmp/dmg_parser.XXXXXX.py)
cat << 'EOF' > "$PARSER_SCRIPT"
import json
import sys
import os

try:
    config_path = os.path.abspath(sys.argv[1])
    config_dir = os.path.dirname(config_path)
    with open(config_path, 'r') as f:
        config = json.load(f)

    def resolve(path):
        if not path:
            return ''
        return path if os.path.isabs(path) else os.path.abspath(os.path.join(config_dir, path))

    # Required fields
    print(f"APP_NAME='{config['app_name']}'")
    print(f"VERSION='{config['version']}'")
    print(f"VOLUME_NAME='{config['volume_name']}'")
    print(f"SOURCE_APP='{resolve(config['source_app'])}'")

    # Window settings
    window = config.get('window', {})
    print(f"WINDOW_X={window.get('x', 200)}")
    print(f"WINDOW_Y={window.get('y', 200)}")
    print(f"WINDOW_WIDTH={window.get('width', 540)}")
    print(f"WINDOW_HEIGHT={window.get('height', 550)}")

    # Icon settings
    icon = config.get('icon_settings', {})
    print(f"ICON_SIZE={icon.get('size', 100)}")
    print(f"TEXT_SIZE={icon.get('text_size', 12)}")

    # Optional fields with defaults
    print(f"BACKGROUND_IMAGE='{resolve(config.get('background_image', ''))}'")
    print(f"VOLUME_ICON='{resolve(config.get('volume_icon', ''))}'")

    # Additional files to include
    files = [resolve(path) for path in config.get('additional_files', [])]
    print(f"ADDITIONAL_FILES='{json.dumps(files)}'")

    # Icon positions - convert to bash associative array format
    positions = config.get('icon_positions', {})
    for name, coords in positions.items():
        # Remove .app extension and spaces for variable names
        var_name = name.replace('.app', '').replace(' ', '_').upper()
        print(f"POS_{var_name}_X={coords['x']}")
        print(f"POS_{var_name}_Y={coords['y']}")

except Exception as e:
    print(f"echo 'Error parsing config: {e}' >&2", file=sys.stderr)
    sys.exit(1)
EOF

eval "$(python3 "$PARSER_SCRIPT" "$CONFIG_FILE")"
rm "$PARSER_SCRIPT"

info "Configuration loaded successfully"
info "Building DMG for: $APP_NAME v$VERSION"

# Define Python script for setting icons via Cocoa
SET_ICON_SCRIPT=$(mktemp /tmp/set_icon.XXXXXX)
mv "$SET_ICON_SCRIPT" "${SET_ICON_SCRIPT}.py"
SET_ICON_SCRIPT="${SET_ICON_SCRIPT}.py"
cat << 'EOF' > "$SET_ICON_SCRIPT"
import Cocoa
import sys
import os

if len(sys.argv) != 3:
    print("Usage: set_icon.py <icon_path> <target_path>")
    sys.exit(1)

icon_path = sys.argv[1]
target_path = sys.argv[2]

if not os.path.exists(icon_path):
    print(f"Error: Icon not found at {icon_path}")
    sys.exit(1)

image = Cocoa.NSImage.alloc().initWithContentsOfFile_(icon_path)
if image:
    success = Cocoa.NSWorkspace.sharedWorkspace().setIcon_forFile_options_(image, target_path, 0)
    if success:
        print(f"Icon set for {target_path}")
    else:
        print(f"Failed to set icon for {target_path}")
        sys.exit(1)
else:
    print("Failed to load icon image")
    sys.exit(1)
EOF

################################################################################
# STEP 2: Setup Build Environment
################################################################################

# Generate DMG filename (omit version segment if empty)
if [ -n "$VERSION" ]; then
    DMG_NAME="${APP_NAME}-${VERSION}.dmg"
else
    DMG_NAME="${APP_NAME}.dmg"
fi
TEMP_DMG_FOLDER="./temp-dmg-$$"  # $$ adds process ID to avoid conflicts
DMG_TEMPLATE_FOLDER="./dmg-template"

# Clean up any existing temp folders from previous failed builds
rm -rf ./temp-dmg-*

info "Creating temporary staging folder: $TEMP_DMG_FOLDER"
mkdir -p "$TEMP_DMG_FOLDER"

################################################################################
# STEP 3: Stage Files for DMG
################################################################################

# Copy the main application
if [ ! -d "$SOURCE_APP" ]; then
    error "Source application not found: $SOURCE_APP"
fi

info "Copying application: $SOURCE_APP"
cp -R "$SOURCE_APP" "$TEMP_DMG_FOLDER/"

# Create Applications symlink (standard for DMG installers)
info "Creating Applications symlink"
ln -s /Applications "$TEMP_DMG_FOLDER/Applications"

# Copy additional files (LICENSE, README, etc.)
if [ -n "$ADDITIONAL_FILES" ] && [ "$ADDITIONAL_FILES" != "[]" ]; then
    info "Copying additional files"
    python3 << EOF
import json
import shutil
import os

files = json.loads('$ADDITIONAL_FILES')
for file_path in files:
    if os.path.exists(file_path):
        print(f"  - {file_path}")
        shutil.copy(file_path, "$TEMP_DMG_FOLDER/")
    else:
        print(f"  ! Warning: {file_path} not found, skipping")
EOF
fi

################################################################################
# STEP 4: Apply Visual Styling
################################################################################

# Copy saved .DS_Store if it exists (preserves window layout)
if [ -f "$DMG_TEMPLATE_FOLDER/.DS_Store" ]; then
    info "Applying saved window layout (.DS_Store)"
    cp "$DMG_TEMPLATE_FOLDER/.DS_Store" "$TEMP_DMG_FOLDER/.DS_Store"
else
    warn "No .DS_Store template found - will create layout with AppleScript"
fi

# Copy background image if specified
if [ -n "$BACKGROUND_IMAGE" ] && [ -f "$BACKGROUND_IMAGE" ]; then
    info "Adding background image"
    mkdir -p "$TEMP_DMG_FOLDER/.background"
    cp "$BACKGROUND_IMAGE" "$TEMP_DMG_FOLDER/.background/background.png"
fi

################################################################################
# STEP 5: Create Initial DMG (Read/Write)
################################################################################

TEMP_DMG="temp-${DMG_NAME}"

info "Creating temporary read-write DMG"
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$TEMP_DMG_FOLDER" \
    -format UDRW \
    -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" \
    "$TEMP_DMG"

################################################################################
# STEP 6: Mount and Style the DMG with AppleScript
################################################################################

info "Mounting DMG for styling"
MOUNT_OUTPUT=$(hdiutil attach -readwrite -noverify -noautoopen "$TEMP_DMG" | grep "/Volumes/")
DEVICE=$(echo "$MOUNT_OUTPUT" | awk '{print $1}')
MOUNT_POINT=$(echo "$MOUNT_OUTPUT" | sed 's/^.*\/Volumes/\/Volumes/')

info "Mounted at: $MOUNT_POINT"

# Give Finder time to recognize the volume
sleep 2

# Apply visual styling using AppleScript
info "Applying Finder window styling"

# Calculate window bounds for AppleScript (left, top, right, bottom)
WINDOW_LEFT=$WINDOW_X
WINDOW_TOP=$WINDOW_Y
WINDOW_RIGHT=$((WINDOW_X + WINDOW_WIDTH))
WINDOW_BOTTOM=$((WINDOW_Y + WINDOW_HEIGHT))

# Build the icon position commands dynamically
POS_SCRIPT=$(mktemp /tmp/dmg_pos.XXXXXX.py)
cat << 'EOF' > "$POS_SCRIPT"
import json
import sys

config_file = sys.argv[1]
mount_point = sys.argv[2]

with open(config_file, 'r') as f:
    config = json.load(f)

positions = config.get('icon_positions', {})
for item_name, coords in positions.items():
    # Escape single quotes in item names
    safe_name = item_name.replace("'", "'\\''")
    print(f"            set position of item \"{safe_name}\" to {{{coords['x']}, {coords['y']}}}")
EOF

ICON_POSITION_SCRIPT=$(python3 "$POS_SCRIPT" "$CONFIG_FILE" "$MOUNT_POINT")
rm "$POS_SCRIPT"

# Construct background script if background image exists
if [ -n "$BACKGROUND_IMAGE" ] && [ -f "$BACKGROUND_IMAGE" ]; then
    BACKGROUND_SCRIPT="set background picture of theViewOptions to file \".background:background.png\""
else
    BACKGROUND_SCRIPT="-- No background image"
fi

# Copy volume icon if specified
if [ -n "$VOLUME_ICON" ] && [ -f "$VOLUME_ICON" ]; then
    info "Setting volume icon"
    cp "$VOLUME_ICON" "$MOUNT_POINT/.VolumeIcon.icns"
    # Try SetFile first if available
    if command -v SetFile &> /dev/null; then
        SetFile -c icnC "$MOUNT_POINT/.VolumeIcon.icns"
        SetFile -a C "$MOUNT_POINT"
    else
        # Fallback to Python/Cocoa for volume icon setting
        info "SetFile not found, using Cocoa to set volume icon"
        python3 "$SET_ICON_SCRIPT" "$VOLUME_ICON" "$MOUNT_POINT" || true
    fi
    # Touch to refresh
    touch "$MOUNT_POINT"
fi

# Execute the AppleScript to style the Finder window
osascript << EOF
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open

        -- Set window properties
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {$WINDOW_LEFT, $WINDOW_TOP, $WINDOW_RIGHT, $WINDOW_BOTTOM}

        -- Set icon view options
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to $ICON_SIZE
        set text size of theViewOptions to $TEXT_SIZE
        $BACKGROUND_SCRIPT

        -- Position icons
        try
$ICON_POSITION_SCRIPT
        end try

        -- Force update
        update without registering applications
        delay 2

        close
    end tell
end tell
EOF

info "Styling applied successfully"

################################################################################
# STEP 7: Finalize and Compress DMG
################################################################################

# Give time for changes to be written
sleep 2

info "Unmounting temporary DMG"
hdiutil detach "$DEVICE"

# Remove old DMG if it exists
[ -f "$DMG_NAME" ] && rm "$DMG_NAME"

info "Creating final compressed DMG"
hdiutil convert "$TEMP_DMG" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "$DMG_NAME"

# Apply icon to the final DMG file
if [ -n "$VOLUME_ICON" ] && [ -f "$VOLUME_ICON" ]; then
    info "Setting icon on DMG file"
    python3 "$SET_ICON_SCRIPT" "$VOLUME_ICON" "$DMG_NAME" || warn "Failed to set DMG file icon"
fi

################################################################################
# STEP 8: Cleanup
################################################################################

info "Cleaning up temporary files"
rm -rf "$TEMP_DMG_FOLDER"
rm "$TEMP_DMG"
rm "$SET_ICON_SCRIPT"

################################################################################
# DONE!
################################################################################

echo ""
info "✓ DMG created successfully: $DMG_NAME"
info "  Size: $(du -h "$DMG_NAME" | cut -f1)"
echo ""

# Optional: Open the DMG to verify
read -p "Would you like to open the DMG to verify? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "$DMG_NAME"
fi
