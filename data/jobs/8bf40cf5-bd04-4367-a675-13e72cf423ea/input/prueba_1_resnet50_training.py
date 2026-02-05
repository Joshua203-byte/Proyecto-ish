"""
Prueba 1: Entrenamiento de ResNet-50 con datos sintéticos
Benchmark pesado de GPU para clasificación de imágenes
"""
import torch
import torch.nn as nn
import torch.optim as optim
import time
import argparse

print("=" * 60)
print("PRUEBA 1: ResNet-50 Training Benchmark")
print("=" * 60)

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--epochs', type=int, default=5, help='Number of epochs')
parser.add_argument('--batch-size', type=int, default=64, help='Batch size')
parser.add_argument('--image-size', type=int, default=224, help='Image size')
args = parser.parse_args()

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n✓ Device: {device}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Model: ResNet-50
print("\n[1/4] Loading ResNet-50...")
from torchvision.models import resnet50
model = resnet50(weights=None, num_classes=1000).to(device)
print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")

# Synthetic data
print(f"\n[2/4] Creating synthetic dataset...")
print(f"  Batch size: {args.batch_size}")
print(f"  Image size: {args.image_size}x{args.image_size}")

class SyntheticDataset(torch.utils.data.Dataset):
    def __init__(self, size, num_samples=10000):
        self.size = size
        self.num_samples = num_samples
    def __len__(self):
        return self.num_samples
    def __getitem__(self, idx):
        img = torch.randn(3, self.size, self.size)
        label = torch.randint(0, 1000, (1,)).item()
        return img, label

dataset = SyntheticDataset(args.image_size)
loader = torch.utils.data.DataLoader(dataset, batch_size=args.batch_size, 
                                      shuffle=True, num_workers=4, pin_memory=True)

# Training setup
print(f"\n[3/4] Setting up training...")
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
scaler = torch.amp.GradScaler('cuda', enabled=torch.cuda.is_available())

# Training loop
print(f"\n[4/4] Training for {args.epochs} epochs...")
print("-" * 60)

total_start = time.time()
for epoch in range(args.epochs):
    model.train()
    epoch_loss = 0
    epoch_start = time.time()
    
    for batch_idx, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        
        with torch.amp.autocast('cuda', enabled=torch.cuda.is_available()):
            outputs = model(images)
            loss = criterion(outputs, labels)
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        epoch_loss += loss.item()
        
        if (batch_idx + 1) % 20 == 0:
            imgs_per_sec = (batch_idx + 1) * args.batch_size / (time.time() - epoch_start)
            print(f"  Epoch {epoch+1} | Batch {batch_idx+1}/{len(loader)} | "
                  f"Loss: {loss.item():.4f} | Speed: {imgs_per_sec:.1f} img/s")
    
    epoch_time = time.time() - epoch_start
    print(f"  → Epoch {epoch+1} complete: {epoch_time:.2f}s | Avg Loss: {epoch_loss/len(loader):.4f}")

total_time = time.time() - total_start

# Results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Device: {device}")
print(f"Total training time: {total_time:.2f} seconds")
print(f"Average time per epoch: {total_time/args.epochs:.2f} seconds")
print(f"Throughput: {args.epochs * len(dataset) / total_time:.1f} images/second")
print("=" * 60)

# Save results
import json
import os
os.makedirs("/workspace/output", exist_ok=True)
with open("/workspace/output/results.json", "w") as f:
    json.dump({
        "test": "ResNet-50 Training",
        "device": str(device),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "total_time_seconds": round(total_time, 2),
        "throughput_images_per_second": round(args.epochs * len(dataset) / total_time, 1)
    }, f, indent=2)
print("\n✓ Results saved to /workspace/output/results.json")
