#!/bin/bash
# Setup NFS Client on Nodo C (GPU Worker)
# Run as root: sudo ./setup_nfs_client.sh

set -e

# Configuration - EDIT THESE VALUES
NFS_SERVER_IP="${NFS_SERVER_IP:-192.168.1.100}"
MOUNT_POINT="/mnt/home-gpu-cloud"

echo "═══════════════════════════════════════════"
echo "  Home-GPU-Cloud NFS Client Setup"
echo "  Node: C (GPU Worker)"
echo "═══════════════════════════════════════════"

# Install NFS client
echo "[1/4] Installing NFS client..."
apt-get update
apt-get install -y nfs-common

# Create mount point
echo "[2/4] Creating mount point..."
mkdir -p $MOUNT_POINT

# Test NFS server connection
echo "[3/4] Testing connection to NFS server ($NFS_SERVER_IP)..."
showmount -e $NFS_SERVER_IP

# Add to fstab for persistent mount
echo "[4/4] Configuring persistent mount..."
grep -q "home-gpu-cloud" /etc/fstab || cat >> /etc/fstab << EOF

# Home-GPU-Cloud NFS Mount
$NFS_SERVER_IP:/srv/nfs/shared $MOUNT_POINT nfs defaults,_netdev 0 0
EOF

# Mount now
mount $MOUNT_POINT

echo ""
echo "═══════════════════════════════════════════"
echo "  NFS Client setup complete!"
echo ""
echo "  Server:     $NFS_SERVER_IP"
echo "  Mount:      $MOUNT_POINT"
echo ""
echo "  Verify: ls -la $MOUNT_POINT"
echo "═══════════════════════════════════════════"
