#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   EPOCHLY CLOUD - SYSTEM MONITOR (TERMINAL)     ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Check if worker is running
if [ "$(docker ps -q -f name=homegpu-worker)" ]; then
    echo -e "${GREEN}✓ Worker Node Online: DGX Spark${NC}"
else
    echo -e "\033[0;31m✗ Worker Node Offline\033[0m"
    exit 1
fi

echo ""
echo -e "${CYAN}--- GPU STATUS (nvidia-smi) ---${NC}"
# Run nvidia-smi. If it detects Grace Blackwell (GB10/200), we note the Unified Memory architecture.
OUTPUT=$(docker exec homegpu-worker nvidia-smi 2>&1)
echo "$OUTPUT"

if echo "$OUTPUT" | grep -q "GB10"; then
    echo -e "\n${BLUE}ℹ️  ARCHITECTURE NOTE: NVIDIA GB10 (Grace Blackwell) uses UNIFIED MEMORY.${NC}"
    echo -e "${BLUE}    - 'Memory-Usage' reports 'Not Supported' because VRAM is shared with System RAM.${NC}"
    echo -e "${BLUE}    - See 'SYSTEM MEMORY' below for actual usage.${NC}"
fi

echo ""
echo -e "${CYAN}--- ACTIVE CONTAINERS (Jobs) ---${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -v "ngrok\|redis\|db\|api\|frontend"

echo ""
echo -e "${CYAN}--- SYSTEM MEMORY & RESOURCES ---${NC}"
# Show stats for ALL containers to catch running jobs
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo -e "${CYAN}--- DISK USAGE ---${NC}"
# Check NFS mount usage
df -h /home/ish/Proyecto-ish/data | awk 'NR==1 || NR==2'

echo ""
echo -e "${BLUE}=================================================${NC}"
