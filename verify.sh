#!/bin/bash
# STRICT MODE: Any error kills the script
set -e
echo "========================================================"
echo "      DEEP VERIFICATION SUITE - AGENTIC MODE"
echo "========================================================"
BASE="/Users/home/GitHub"
ERRORS=0
log_success() { echo "✅ [PASS] $1"; }
log_fail() { echo "❌ [FAIL] $1"; ERRORS=$((ERRORS+1)); }

# --- Check 1: Symlinks (Config files only - NOT CHANGELOG) ---
for proj in 4Charm iSort LibraLog Nexus Papyrus PyPixPro; do
    # Check .pylintrc
    if [ -L "$BASE/$proj/.pylintrc" ] && [ "$(readlink "$BASE/$proj/.pylintrc")" == "../.dev-tools/_shared-configs/.pylintrc" ]; then
        log_success "$proj .pylintrc is a correct symlink"
    else
        log_fail "$proj .pylintrc is INVALID"
    fi
    # Check pyrightconfig.json
    if [ -L "$BASE/$proj/pyrightconfig.json" ] && [ "$(readlink "$BASE/$proj/pyrightconfig.json")" == "../.dev-tools/_shared-configs/pyrightconfig.json" ]; then
        log_success "$proj pyrightconfig.json is a correct symlink"
    else
        log_fail "$proj pyrightconfig.json is INVALID"
    fi
    # Verify CHANGELOG exists as a REGULAR FILE (not symlink)
    if [ -f "$BASE/$proj/docs/CHANGELOG.md" ] && [ ! -L "$BASE/$proj/docs/CHANGELOG.md" ]; then
        log_success "$proj CHANGELOG.md exists as individual file"
    else
        log_fail "$proj CHANGELOG.md is missing or is a symlink"
    fi
done

# --- Check 2: Git Attributes ---
for proj in 4Charm iSort LibraLog Nexus Papyrus PyPixPro; do
    if grep -q "dmg.*filter=lfs" "$BASE/$proj/.gitattributes"; then
        log_success "$proj .gitattributes contains LFS config"
    else
        log_fail "$proj .gitattributes MISSING or corrupt"
    fi
done

# --- Check 3: Nexus Specifics ---
if [ ! -f "$BASE/Nexus/.markdownlint.json" ]; then
    log_success "Nexus local config correctly removed"
else
    log_fail "Nexus local config STILL EXISTS"
fi
WORKFLOW="$BASE/Nexus/.github/workflows/pylint.yml"
if grep -q "npm install -g markdownlint-cli" "$WORKFLOW"; then
    log_success "Nexus workflow uses NPM"
else
    log_fail "Nexus workflow missing NPM command"
fi
if grep -q "markdown-lint:" "$WORKFLOW"; then
    log_success "Nexus workflow has markdown-lint job"
else
    log_fail "Nexus workflow missing markdown-lint job"
fi

# --- Summary ---
echo "========================================================"
if [ $ERRORS -eq 0 ]; then
    echo "🎉 ALL SYSTEMS VERIFIED. 100% COMPLIANCE ACHIEVED."
    exit 0
else
    echo "🚫 VERIFICATION FAILED WITH $ERRORS ERRORS."
    exit 1
fi
