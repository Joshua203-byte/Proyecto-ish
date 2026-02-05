"""
Prueba 4: CNN Training en CIFAR-10
Entrena una red convolucional en el dataset CIFAR-10 real
"""
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import time
import argparse

print("=" * 60)
print("PRUEBA 4: CNN Training on CIFAR-10")
print("=" * 60)

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
parser.add_argument('--batch-size', type=int, default=128, help='Batch size')
parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
args = parser.parse_args()

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n✓ Device: {device}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")

# CNN Model (similar to VGG)
class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(3, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2),
            # Block 2
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2),
            # Block 3
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.MaxPool2d(2),
            # Block 4
            nn.Conv2d(256, 512, 3, padding=1), nn.BatchNorm2d(512), nn.ReLU(),
            nn.Conv2d(512, 512, 3, padding=1), nn.BatchNorm2d(512), nn.ReLU(),
            nn.Conv2d(512, 512, 3, padding=1), nn.BatchNorm2d(512), nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 2 * 2, 512), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(512, 512), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(512, 10)
        )
    
    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)

# Create model
print("\n[1/4] Building CNN model...")
model = CNN().to(device)
params = sum(p.numel() for p in model.parameters())
print(f"  Parameters: {params:,} ({params/1e6:.1f}M)")

# Load CIFAR-10
print("\n[2/4] Loading CIFAR-10 dataset...")
transform_train = transforms.Compose([
    transforms.RandomCrop(32, padding=4),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
])
transform_test = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
])

trainset = torchvision.datasets.CIFAR10(root='/tmp/data', train=True, download=True, transform=transform_train)
testset = torchvision.datasets.CIFAR10(root='/tmp/data', train=False, download=True, transform=transform_test)

trainloader = torch.utils.data.DataLoader(trainset, batch_size=args.batch_size, shuffle=True, num_workers=2)
testloader = torch.utils.data.DataLoader(testset, batch_size=args.batch_size, shuffle=False, num_workers=2)

print(f"  Training samples: {len(trainset)}")
print(f"  Test samples: {len(testset)}")

# Training setup
print("\n[3/4] Setting up training...")
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=args.lr)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
scaler = torch.amp.GradScaler('cuda', enabled=torch.cuda.is_available())

# Training loop
print(f"\n[4/4] Training for {args.epochs} epochs...")
print("-" * 60)

total_start = time.time()
best_acc = 0

for epoch in range(args.epochs):
    # Train
    model.train()
    train_loss = 0
    correct = 0
    total = 0
    epoch_start = time.time()
    
    for inputs, targets in trainloader:
        inputs, targets = inputs.to(device), targets.to(device)
        
        optimizer.zero_grad()
        with torch.amp.autocast('cuda', enabled=torch.cuda.is_available()):
            outputs = model(inputs)
            loss = criterion(outputs, targets)
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        train_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
    
    scheduler.step()
    train_acc = 100. * correct / total
    
    # Test
    model.eval()
    test_correct = 0
    test_total = 0
    with torch.no_grad():
        for inputs, targets in testloader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            test_total += targets.size(0)
            test_correct += predicted.eq(targets).sum().item()
    
    test_acc = 100. * test_correct / test_total
    best_acc = max(best_acc, test_acc)
    
    epoch_time = time.time() - epoch_start
    print(f"  Epoch {epoch+1:2d}/{args.epochs} | {epoch_time:.1f}s | "
          f"Train: {train_acc:.1f}% | Test: {test_acc:.1f}% | Best: {best_acc:.1f}%")

total_time = time.time() - total_start

# Results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Device: {device}")
print(f"Best Test Accuracy: {best_acc:.2f}%")
print(f"Total training time: {total_time:.2f} seconds")
print(f"Time per epoch: {total_time/args.epochs:.2f} seconds")
print("=" * 60)

# Save
import json, os
os.makedirs("/workspace/output", exist_ok=True)
with open("/workspace/output/results.json", "w") as f:
    json.dump({
        "test": "CIFAR-10 CNN Training",
        "best_accuracy": round(best_acc, 2),
        "epochs": args.epochs,
        "device": str(device),
        "total_time_seconds": round(total_time, 2)
    }, f, indent=2)

# Save model
torch.save(model.state_dict(), "/workspace/output/model.pth")
print("\n✓ Model saved to /workspace/output/model.pth")
