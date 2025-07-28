#!/bin/bash
# This script resets the NVIDIA GPU driver by reloading its kernel modules.
# Run this with sudo after your laptop wakes from sleep.

set -e # Exit immediately if a command exits with a non-zero status.

echo "🛑 Unloading NVIDIA kernel modules..."
sudo rmmod nvidia_uvm
sudo rmmod nvidia_drm
sudo rmmod nvidia_modeset
sudo rmmod nvidia

echo "✅ Kernel modules unloaded."
echo "🚀 Reloading NVIDIA kernel modules..."

sudo modprobe nvidia

echo "✅ GPU driver has been reset. You can now start your application."