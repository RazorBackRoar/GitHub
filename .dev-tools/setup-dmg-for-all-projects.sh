#!/bin/bash

################################################################################
# Setup DMG Builder for All Projects
# This script configures all your GitHub projects to use the universal DMG builder
# and links shared development configurations
################################################################################

set -e

GITHUB_ROOT="/Users/home/GitHub"
UNIVERSAL_SCRIPT="$GITHUB_ROOT/universal_dmg.sh"
SHARED_CONFIGS="$GITHUB_ROOT/.dev-tools/_shared-configs"

# Projects to configure (based on your ls output)
PROJECTS=(
    "Papyrus"
    "Nexus"
    "4Charm"
    "PyPixPro"
    "LibraLog"
    "iSort"
)

# Shared config files to link
SHARED_CONFIG_FILES=(
    "pyrightconfig.json"
    ".pylintrc"
)

echo "================================================"
echo "Universal DMG Builder Setup"
echo "================================================"
echo ""

# Verify universal script exists
if [ ! -f "$UNIVERSAL_SCRIPT" ]; then
    echo "❌ ERROR: Universal script not found at $UNIVERSAL_SCRIPT"
    echo "Please make sure universal_dmg.sh exists in $GITHUB_ROOT"
    exit 1
fi

echo "✓ Found universal script: $UNIVERSAL_SCRIPT"

# Check for shared configs
if [ -d "$SHARED_CONFIGS" ]; then
    echo "✓ Found shared configs: $SHARED_CONFIGS"
else
    echo "⚠️  Warning: Shared configs directory not found at $SHARED_CONFIGS"
    echo "   Will skip linking shared configs"
fi

echo ""

# Function to setup a single project
setup_project() {
    local PROJECT_NAME=$1
    local PROJECT_PATH="$GITHUB_ROOT/$PROJECT_NAME"
    
    echo "──────────────────────────────────────────────"
    echo "Setting up: $PROJECT_NAME"
    echo "──────────────────────────────────────────────"
    
    if [ ! -d "$PROJECT_PATH" ]; then
        echo "⚠️  Skipping $PROJECT_NAME (directory not found)"
        echo ""
        return
    fi
    
    cd "$PROJECT_PATH"
    
    # 1. Create dmg-template folder
    echo "  Creating dmg-template folder..."
    mkdir -p dmg-template
    
    # 2. Create symbolic link to universal script
    echo "  Creating link to universal DMG builder..."
    ln -sf "$UNIVERSAL_SCRIPT" build-dmg.sh
    chmod +x build-dmg.sh
    
    # 3. Link shared development configs
    if [ -d "$SHARED_CONFIGS" ]; then
        echo "  Linking shared development configs..."
        for config in "${SHARED_CONFIG_FILES[@]}"; do
            if [ -f "$SHARED_CONFIGS/$config" ]; then
                # Remove existing file/link if it exists
                [ -e "$config" ] && rm "$config"
                ln -sf "$SHARED_CONFIGS/$config" "$config"
                echo "    ✓ Linked $config"
            else
                echo "    ⚠️  $config not found in shared configs, skipping"
            fi
        done
    fi
    
    # 4. Create dmg-config.json if it doesn't exist
    if [ ! -f "dmg-config.json" ]; then
        echo "  Creating dmg-config.json..."
        cat > dmg-config.json << EOF
{
  "app_name": "$PROJECT_NAME",
  "version": "1.0.0",
  "volume_name": "$PROJECT_NAME Installer",
  "source_app": "./build/$PROJECT_NAME.app",
  
  "window": {
    "x": 200,
    "y": 200,
    "width": 540,
    "height": 550
  },
  
  "icon_settings": {
    "size": 100,
    "text_size": 12
  },
  
  "background_image": "",
  "volume_icon": "",
  
  "additional_files": [
    "LICENSE",
    "README.md"
  ],
  
  "icon_positions": {
    "$PROJECT_NAME.app": {"x": 140, "y": 120},
    "Applications": {"x": 400, "y": 120},
    "LICENSE": {"x": 140, "y": 340},
    "README.md": {"x": 400, "y": 340}
  }
}
EOF
    else
        echo "  ✓ dmg-config.json already exists, skipping..."
    fi
    
    # 5. Update .gitignore
    echo "  Updating .gitignore..."
    
    # Check if .gitignore exists
    if [ ! -f ".gitignore" ]; then
        echo "  Creating .gitignore..."
        touch .gitignore
    fi
    
    # Check if DS_Store rules already exist
    if ! grep -q "dmg-template/.DS_Store" .gitignore; then
        cat >> .gitignore << 'EOF'

# macOS Finder metadata
.DS_Store
**/.DS_Store
.AppleDouble
.LSOverride

# But allow DMG template
!dmg-template/.DS_Store

# DMG build artifacts
temp-dmg-*
*.dmg

# Shared dev configs (symlinked from .dev-tools)
pyrightconfig.json
.pylintrc
EOF
        echo "  ✓ Added .gitignore rules"
    else
        echo "  ✓ .gitignore already configured"
    fi
    
    # 6. Create README for DMG building
    if [ ! -f "DMG_BUILD_README.md" ]; then
        cat > DMG_BUILD_README.md << EOF
# Building DMG for $PROJECT_NAME

## Quick Start

\`\`\`bash
./build-dmg.sh
\`\`\`

## Configuration

Edit \`dmg-config.json\` to customize:
- Window size and position
- Icon positions
- Background image
- Volume icon
- Additional files to include

## Shared Development Configs

This project uses symlinked configs from \`.dev-tools/_shared-configs/\`:
- \`pyrightconfig.json\` - Type checking configuration
- \`.pylintrc\` - Linting configuration

To override for this project only, delete the symlink and create a local file.

## Creating the .DS_Store Template

1. Create a test folder that matches your DMG layout
2. Arrange icons exactly as you want them
3. Close the Finder window
4. Copy the .DS_Store to dmg-template/

\`\`\`bash
mkdir test-layout
cd test-layout
# Add your files and arrange them
cd ..
cp test-layout/.DS_Store dmg-template/.DS_Store
rm -rf test-layout
\`\`\`

## Troubleshooting

- If window size is wrong, check \`window\` settings in dmg-config.json
- If icons aren't positioned, verify names in \`icon_positions\` match exactly
- To force AppleScript styling, remove dmg-template/.DS_Store
EOF
    fi
    
    echo "  ✓ Setup complete for $PROJECT_NAME"
    echo ""
}

# Setup all projects
for PROJECT in "${PROJECTS[@]}"; do
    setup_project "$PROJECT"
done

echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "Next steps for each project:"
echo "1. cd /Users/home/GitHub/[ProjectName]"
echo "2. Review and adjust dmg-config.json"
echo "3. Create .DS_Store template (see DMG_BUILD_README.md)"
echo "4. Run: ./build-dmg.sh"
echo ""
echo "Projects configured:"
for PROJECT in "${PROJECTS[@]}"; do
    echo "  • $PROJECT"
done
echo ""
echo "Shared configs linked:"
for config in "${SHARED_CONFIG_FILES[@]}"; do
    echo "  • $config"
done
echo ""
