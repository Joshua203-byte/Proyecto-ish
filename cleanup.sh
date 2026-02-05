#!/bin/bash
# Gotham Cloud - System Cleanup Script
# Removes Docker remnants (stopped containers, unused images) and temp files.

echo "🧹 Starting System Cleanup..."

# 1. Docker Prune
# Removes all stopped containers, all networks not used by at least one container,
# and all dangling images.
echo "🐳 Pruning Docker System..."
docker container prune -f
docker network prune -f
docker image prune -f

# Note: We do NOT prune volumes automatically to preserve persistent data.
# Note: We do NOT prune all images (-a) to avoid deleting cached build layers.

# 2. Python Cache
echo "🐍 Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "✅ Cleanup Complete! No remnants left."
