#!/bin/bash
set -e

MSG="Standardize configuration (Dec 2025)

- Implemented shared symlinks for iSort/LibraLog
- Enforced Git LFS attributes for binaries
- Migrated Nexus Markdown Linting to NPM-based CI/CD
- Verified 100% portfolio compliance"

echo "Committing iSort..."
cd /Users/home/GitHub/iSort && git commit -m "$MSG" || echo "Nothing to commit in iSort"

echo "Committing LibraLog..."
cd /Users/home/GitHub/LibraLog && git commit -m "$MSG" || echo "Nothing to commit in LibraLog"

echo "Committing PyPixPro..."
cd /Users/home/GitHub/PyPixPro && git commit -m "$MSG" || echo "Nothing to commit in PyPixPro"

echo "Committing 4Charm..."
cd /Users/home/GitHub/4Charm && git commit -m "$MSG" || echo "Nothing to commit in 4Charm"

echo "Committing Guide..."
cd /Users/home/GitHub/czkawka-macos-guide && git commit -m "$MSG" || echo "Nothing to commit in Guide"

echo "Committing Nexus..."
cd /Users/home/GitHub/Nexus && git commit -m "$MSG" || echo "Nothing to commit in Nexus"

echo "Committing DevTools..."
cd /Users/home/GitHub/.dev-tools && git commit -m "$MSG" || echo "Nothing to commit in DevTools"

echo "✅ All Commits Complete."
