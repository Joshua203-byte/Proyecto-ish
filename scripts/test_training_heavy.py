#!/usr/bin/env python3
"""
Neural Network Training Test
Trains a simple CNN on synthetic data to test GPU training capabilities
Expected runtime: 5-10 minutes
"""
import torch
import torch.nn as nn
import torch.optim as optim
import time
import json
from pathlib import Path

print("=" * 60)
print("🧠 NEURAL NETWORK TRAINING TEST")
print("=" * 60)

# Check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\nDevice: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Model definition - ResNet-like architecture
class HeavyCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(256, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.Conv2d(512, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            nn.Conv2d(512, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 100),
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

# Parameters
BATCH_SIZE = 64
IMAGE_SIZE = 224
NUM_BATCHES = 100
EPOCHS = 3

print(f"\nBatch size: {BATCH_SIZE}")
print(f"Image size: {IMAGE_SIZE}x{IMAGE_SIZE}")
print(f"Batches per epoch: {NUM_BATCHES}")
print(f"Epochs: {EPOCHS}")

# Create model
print("\n📦 Creating model...")
model = HeavyCNN().to(device)
num_params = sum(p.numel() for p in model.parameters())
print(f"Model parameters: {num_params:,}")

# Optimizer and loss
optimizer = optim.AdamW(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Training loop
print("\n🏋️ Starting training...")
total_start = time.perf_counter()
epoch_times = []

for epoch in range(EPOCHS):
    epoch_start = time.perf_counter()
    model.train()
    total_loss = 0
    
    for batch_idx in range(NUM_BATCHES):
        # Generate synthetic data
        data = torch.randn(BATCH_SIZE, 3, IMAGE_SIZE, IMAGE_SIZE, device=device)
        target = torch.randint(0, 100, (BATCH_SIZE,), device=device)
        
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
        if (batch_idx + 1) % 20 == 0:
            print(f"  Epoch {epoch+1}/{EPOCHS} - Batch {batch_idx+1}/{NUM_BATCHES} - Loss: {loss.item():.4f}")
    
    epoch_time = time.perf_counter() - epoch_start
    epoch_times.append(epoch_time)
    avg_loss = total_loss / NUM_BATCHES
    samples_per_sec = (BATCH_SIZE * NUM_BATCHES) / epoch_time
    
    print(f"\n📊 Epoch {epoch+1} complete:")
    print(f"   Time: {epoch_time:.1f}s")
    print(f"   Avg Loss: {avg_loss:.4f}")
    print(f"   Throughput: {samples_per_sec:.1f} samples/sec")
    print()

total_time = time.perf_counter() - total_start

# Results
print("=" * 60)
print("📈 TRAINING RESULTS")
print("=" * 60)
print(f"Total training time: {total_time:.1f} seconds")
print(f"Average epoch time: {sum(epoch_times)/len(epoch_times):.1f} seconds")
print(f"Total samples processed: {BATCH_SIZE * NUM_BATCHES * EPOCHS:,}")
print(f"Average throughput: {(BATCH_SIZE * NUM_BATCHES * EPOCHS) / total_time:.1f} samples/sec")
print(f"GPU Memory Peak: {torch.cuda.max_memory_allocated() / 1024**3:.2f} GB")

# Save results
results = {
    "test": "neural_network_training",
    "model_params": num_params,
    "batch_size": BATCH_SIZE,
    "epochs": EPOCHS,
    "total_time_sec": total_time,
    "avg_epoch_time_sec": sum(epoch_times) / len(epoch_times),
    "samples_per_sec": (BATCH_SIZE * NUM_BATCHES * EPOCHS) / total_time,
    "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
    "memory_peak_gb": torch.cuda.max_memory_allocated() / 1024**3
}

output_path = Path("/tmp/training_test_results.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n💾 Results saved to: {output_path}")

print("\n✅ TRAINING TEST COMPLETE!")
