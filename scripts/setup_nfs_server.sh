#!/bin/bash
# Setup NFS Server on Nodo B (NAS)
# Run as root: sudo ./setup_nfs_server.sh

set -e

echo "═══════════════════════════════════════════"
echo "  Home-GPU-Cloud NFS Server Setup"
echo "  Node: B (NAS/Storage)"
echo "═══════════════════════════════════════════"

# Install NFS server
echo "[1/4] Installing NFS server..."
apt-get update
apt-get install -y nfs-kernel-server

# Create shared directory
echo "[2/4] Creating shared directory..."
mkdir -p /srv/nfs/shared/jobs
chown -R nobody:nogroup /srv/nfs/shared
chmod -R 755 /srv/nfs/shared

# Configure exports
echo "[3/4] Configuring NFS exports..."
cat >> /etc/exports << EOF

# Home-GPU-Cloud Shared Storage
# Allow access from local network (adjust subnet as needed)
/srv/nfs/shared 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)
EOF

# Restart NFS server
echo "[4/4] Restarting NFS server..."
exportfs -a
systemctl restart nfs-kernel-server
systemctl enable nfs-kernel-server

echo ""
echo "═══════════════════════════════════════════"
echo "  NFS Server setup complete!"
echo ""
echo "  Exported: /srv/nfs/shared"
echo "  Network:  192.168.1.0/24"
echo ""
echo "  Test from client: showmount -e $(hostname -I | awk '{print $1}')"
echo "═══════════════════════════════════════════"
