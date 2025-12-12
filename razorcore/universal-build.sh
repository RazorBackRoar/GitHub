#!/opt/homebrew/bin/bash
# =============================================================================
# Universal Build Script for RazorBackRoar's macOS Applications
# =============================================================================
# This script builds any of the supported apps into a signed .app and .dmg
#
# Usage:
#   ./universal-build.sh <project_name>
#   ./universal-build.sh 4Charm
#   ./universal-build.sh iSort
#   ./universal-build.sh --help
#
# Supported projects: 4Charm, Nexus, Papyrus, PyPixPro, iSort
# =============================================================================

set -euo pipefail

# ANSI Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Workspace root (parent of razorcore)
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"

# Python executable - prefer 3.13, fall back to 3.12, 3.11, etc.
find_python() {
    for version in 3.13 3.12 3.11 3.10; do
        if command -v "python${version}" &> /dev/null; then
            echo "python${version}"
            return
        fi
        if [ -x "/opt/homebrew/bin/python${version}" ]; then
            echo "/opt/homebrew/bin/python${version}"
            return
        fi
    done

    # Fallback to python3
    if command -v python3 &> /dev/null; then
        echo "python3"
        return
    fi

    echo ""
}

PYTHON_EXE=$(find_python)

# Project configurations
declare -A PROJECT_PATHS=(
    ["4Charm"]="4Charm"
    ["Nexus"]="Nexus"
    ["Papyrus"]="Papyrus"
    ["PyPixPro"]="PyPixPro"
    ["iSort"]="iSort"
)

declare -A PROJECT_PACKAGES=(
    ["4Charm"]="four_charm"
    ["Nexus"]="nexus"
    ["Papyrus"]="papyrus"
    ["PyPixPro"]="pypixpro"
    ["iSort"]="isort"
)

declare -A PROJECT_ICONS=(
    ["4Charm"]="assets/icons/4Charm.icns"
    ["Nexus"]="assets/icons/Nexus.icns"
    ["Papyrus"]="assets/icons/papyrus.icns"
    ["PyPixPro"]="assets/icons/pypixpro.icns"
    ["iSort"]="assets/icons/iSort.icns"
)

# Code signing identity (ad-hoc by default)
CODESIGN_IDENTITY="${CODESIGN_IDENTITY:--}"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "\n${BLUE}[$1]${NC} $2"
}

print_success() {
    echo -e "   ${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "   ${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "   ${RED}✗${NC} $1"
}

show_help() {
    echo -e "${CYAN}Universal Build Script${NC} - Build macOS applications"
    echo ""
    echo "Usage: $0 <project_name> [options]"
    echo ""
    echo "Projects:"
    echo "  4Charm      - 4chan media downloader"
    echo "  Nexus       - Safari URL automation"
    echo "  Papyrus     - HTML converter"
    echo "  PyPixPro    - Photo organization"
    echo "  iSort       - Apple device file organizer"
    echo ""
    echo "Options:"
    echo "  --help, -h      Show this help message"
    echo "  --clean-only    Only clean build artifacts"
    echo "  --no-dmg        Skip DMG creation"
    echo "  --list          List available projects"
    echo ""
    echo "Environment Variables:"
    echo "  CODESIGN_IDENTITY    Code signing identity (default: - for ad-hoc)"
    echo ""
    echo "Examples:"
    echo "  $0 4Charm"
    echo "  $0 iSort --no-dmg"
    echo "  CODESIGN_IDENTITY='Developer ID' $0 Nexus"
}

get_pyproject_version() {
    local project_path="$1"
    "$PYTHON_EXE" - "$project_path" <<'PY'
import pathlib, re, sys
project_path = pathlib.Path(sys.argv[1])
pyproject = project_path / 'pyproject.toml'
if not pyproject.exists():
    print('0.0.0')
    sys.exit(0)
match = re.search(r'version\s*=\s*"([^"\n]+)"', pyproject.read_text(encoding='utf-8'))
print(match.group(1) if match else '0.0.0')
PY
}

eject_volume() {
    local volume_name="$1"
    if hdiutil info 2>/dev/null | grep -q "/Volumes/${volume_name}"; then
        echo -e "   ${YELLOW}Ejecting mounted ${volume_name} volume...${NC}"
        hdiutil detach "/Volumes/${volume_name}" -force 2>/dev/null || true
        sleep 1
    fi
}

clean_build_artifacts() {
    local project_path="$1"

    rm -rf "${project_path}/build/temp" 2>/dev/null || true
    rm -rf "${project_path}/build/dist" 2>/dev/null || true
    rm -rf "${project_path}"/*.egg-info 2>/dev/null || true
    rm -rf "${project_path}/src"/*.egg-info 2>/dev/null || true
    find "${project_path}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${project_path}" -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -f "${project_path}"/*.dmg 2>/dev/null || true
}

# =============================================================================
# Main Build Function
# =============================================================================

build_project() {
    local APP_NAME="$1"
    local SKIP_DMG="${2:-false}"

    # Validate project
    if [[ ! -v PROJECT_PATHS[$APP_NAME] ]]; then
        print_error "Unknown project: $APP_NAME"
        echo "Available projects: ${!PROJECT_PATHS[*]}"
        exit 1
    fi

    local PROJECT_DIR="${WORKSPACE_ROOT}/${PROJECT_PATHS[$APP_NAME]}"
    local PACKAGE_NAME="${PROJECT_PACKAGES[$APP_NAME]}"
    local ICON_PATH="${PROJECT_ICONS[$APP_NAME]:-}"

    # Validate project directory
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi

    # Get version
    local APP_VERSION=$(get_pyproject_version "$PROJECT_DIR")

    print_header "Building ${APP_NAME} v${APP_VERSION}"

    # Change to project directory
    cd "$PROJECT_DIR"

    # Step 1: Eject any mounted volumes
    print_step "1/7" "Checking for mounted volumes..."
    eject_volume "$APP_NAME"
    print_success "No conflicting volumes"

    # Step 2: Check Python
    print_step "2/7" "Checking Python environment..."
    if [ -z "$PYTHON_EXE" ]; then
        print_error "Python 3.10+ not found"
        exit 1
    fi
    print_success "Using $($PYTHON_EXE --version)"

    # Step 3: Install dependencies
    print_step "3/7" "Installing dependencies..."
    if [ -f "requirements.txt" ]; then
        "$PYTHON_EXE" -m pip install -r requirements.txt -q
    fi
    "$PYTHON_EXE" -m pip install py2app -q
    print_success "Dependencies installed"

    # Step 4: Check icon
    print_step "4/7" "Verifying app icon..."
    if [ -n "$ICON_PATH" ] && [ -f "$ICON_PATH" ]; then
        print_success "Icon found: $ICON_PATH"
    else
        print_warning "Icon not found, will use default"
    fi

    # Step 5: Clean old builds
    print_step "5/7" "Cleaning build artifacts..."
    clean_build_artifacts "$PROJECT_DIR"
    print_success "Cleanup complete"

    # Step 6: Build .app bundle
    print_step "6/7" "Building .app bundle (ARM64)..."
    mkdir -p build/dist

    if [ -f "setup.py" ]; then
        "$PYTHON_EXE" setup.py py2app --arch=arm64 2>&1 | tee build/build.log || {
            print_error "Build failed - check build/build.log"
            exit 1
        }
    else
        print_error "setup.py not found"
        exit 1
    fi

    local APP_PATH="build/dist/${APP_NAME}.app"
    if [ ! -d "$APP_PATH" ]; then
        # Try alternative locations
        APP_PATH="dist/${APP_NAME}.app"
    fi

    if [ ! -d "$APP_PATH" ]; then
        print_error "App bundle not created"
        exit 1
    fi
    print_success "App bundle created: $APP_PATH"

    # Code sign
    echo -e "   ${BLUE}Signing app...${NC}"
    codesign --force --deep --sign "$CODESIGN_IDENTITY" "$APP_PATH"
    print_success "App signed"

    # Step 7: Create DMG
    if [ "$SKIP_DMG" = "false" ]; then
        print_step "7/7" "Creating DMG..."

        local DMG_PATH="build/dist/${APP_NAME}.dmg"
        local DMG_STAGING="build/dist/${APP_NAME}_dmg"
        local DMG_TEMP="build/dist/${APP_NAME}_temp.dmg"

        rm -f "$DMG_PATH" "$DMG_TEMP"
        rm -rf "$DMG_STAGING"
        mkdir -p "$DMG_STAGING"

        cp -R "$APP_PATH" "$DMG_STAGING/"
        ln -s /Applications "$DMG_STAGING/Applications" 2>/dev/null || true
        rm -f "$DMG_STAGING/.DS_Store"

        # Create read-write DMG
        hdiutil create -volname "${APP_NAME}" -srcfolder "$DMG_STAGING" -ov -format UDRW "$DMG_TEMP"

        # Style the DMG
        echo -e "   ${BLUE}Styling DMG window...${NC}"
        DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "$DMG_TEMP" | egrep '^/dev/' | sed 1q | awk '{print $1}')
        sleep 2

        osascript <<EOF
tell application "Finder"
    tell disk "${APP_NAME}"
        open
        delay 1
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {200, 200, 740, 520}
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 100
        set position of item "${APP_NAME}.app" of container window to {140, 130}
        set position of item "Applications" of container window to {400, 130}
        update without registering applications
        delay 1
        close
    end tell
end tell
EOF

        hdiutil detach "$DEVICE" -force
        hdiutil convert "$DMG_TEMP" -format UDZO -o "$DMG_PATH"

        rm -f "$DMG_TEMP"
        rm -rf "$DMG_STAGING"

        local DMG_SIZE=$(du -sh "$DMG_PATH" | cut -f1)
        print_success "DMG created: $DMG_PATH ($DMG_SIZE)"
    else
        print_step "7/7" "Skipping DMG creation"
    fi

    # Cleanup
    rm -rf "$APP_PATH" build/temp "${PROJECT_DIR}"/*.egg-info "${PROJECT_DIR}/src"/*.egg-info 2>/dev/null || true

    # Final summary
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✅ Build Complete: ${APP_NAME} v${APP_VERSION}${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ "$SKIP_DMG" = "false" ]; then
        echo -e "\n${CYAN}📀 To install:${NC} open 'build/dist/${APP_NAME}.dmg'"
    fi
    echo ""
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    local PROJECT=""
    local SKIP_DMG="false"
    local CLEAN_ONLY="false"

    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --list)
                echo "Available projects:"
                for proj in "${!PROJECT_PATHS[@]}"; do
                    echo "  - $proj"
                done
                exit 0
                ;;
            --clean-only)
                CLEAN_ONLY="true"
                shift
                ;;
            --no-dmg)
                SKIP_DMG="true"
                shift
                ;;
            *)
                PROJECT="$1"
                shift
                ;;
        esac
    done

    if [ -z "$PROJECT" ]; then
        print_error "No project specified"
        show_help
        exit 1
    fi

    if [ "$CLEAN_ONLY" = "true" ]; then
        local PROJECT_DIR="${WORKSPACE_ROOT}/${PROJECT_PATHS[$PROJECT]:-$PROJECT}"
        if [ -d "$PROJECT_DIR" ]; then
            print_step "1/1" "Cleaning $PROJECT..."
            clean_build_artifacts "$PROJECT_DIR"
            print_success "Cleanup complete"
        else
            print_error "Project not found: $PROJECT"
        fi
        exit 0
    fi

    build_project "$PROJECT" "$SKIP_DMG"
}

main "$@"
