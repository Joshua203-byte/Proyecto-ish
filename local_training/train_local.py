#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           LOCAL AI TRAINING — CPU BENCHMARK                      ║
║                                                                  ║
║  This script trains a real neural network (VGG-style CNN) on     ║
║  the CIFAR-10 dataset using ONLY your CPU.                       ║
║                                                                  ║
║  Purpose: Demonstrate how slow local CPU training is compared    ║
║  to Epochly's GPU infrastructure.                                ║
║                                                                  ║
║  Upload this same script to Epochly to see a massive speedup!    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import time
import os
import json
import sys
import platform

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
EPOCHS = 5
BATCH_SIZE = 64
LEARNING_RATE = 0.001
NUM_WORKERS = 2

# Output directory (relative to this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
DATA_DIR = os.path.join(SCRIPT_DIR, "data")


# ═══════════════════════════════════════════════════════════════
# COLORS FOR TERMINAL OUTPUT
# ═══════════════════════════════════════════════════════════════
class C:
    """ANSI color codes for terminal styling."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def print_banner():
    """Print the startup banner."""
    print(f"\n{C.BOLD}{C.CYAN}")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                        ║")
    print("  ║        🖥️  LOCAL AI TRAINING — CPU MODE                 ║")
    print("  ║                                                        ║")
    print("  ║   Training a real neural network on YOUR computer       ║")
    print("  ║   This will take a while... grab a coffee ☕            ║")
    print("  ║                                                        ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")


def format_time(seconds):
    """Format seconds into human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def print_system_info():
    """Print system information."""
    print(f"\n{C.BOLD}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}  SYSTEM INFORMATION{C.RESET}")
    print(f"{'═' * 60}")
    print(f"  {C.DIM}OS:{C.RESET}           {platform.system()} {platform.release()}")
    print(f"  {C.DIM}Machine:{C.RESET}      {platform.machine()}")
    print(f"  {C.DIM}Processor:{C.RESET}    {platform.processor() or 'Unknown'}")
    print(f"  {C.DIM}Python:{C.RESET}       {platform.python_version()}")
    print(f"  {C.DIM}PyTorch:{C.RESET}      {torch.__version__}")

    # Force CPU mode
    device = torch.device("cpu")
    print(f"  {C.DIM}Device:{C.RESET}       {C.YELLOW}CPU (forced — no GPU acceleration){C.RESET}")
    print(f"  {C.DIM}Threads:{C.RESET}      {torch.get_num_threads()}")
    print(f"{'═' * 60}\n")
    return device


# ═══════════════════════════════════════════════════════════════
# NEURAL NETWORK MODEL (VGG-style Deep CNN)
# ═══════════════════════════════════════════════════════════════
class DeepCNN(nn.Module):
    """
    VGG-style convolutional neural network for image classification.
    Architecture: 3 conv blocks (each with 2 conv layers) + 2 FC layers
    Total parameters: ~3.5 million
    """
    def __init__(self, num_classes=10):
        super(DeepCNN, self).__init__()

        # Feature extraction layers
        self.features = nn.Sequential(
            # Block 1: 3 -> 64 channels
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 2: 64 -> 128 channels
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 3: 128 -> 256 channels
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        # Classification layers
        self.classifier = nn.Sequential(
            nn.Linear(256 * 4 * 4, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


def count_parameters(model):
    """Count total trainable parameters in the model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# ═══════════════════════════════════════════════════════════════
# TRAINING FUNCTION
# ═══════════════════════════════════════════════════════════════
def train(model, device, trainloader, testloader, epochs):
    """
    Train the model and return training history.
    """
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

    history = {
        "epochs": [],
        "train_loss": [],
        "train_accuracy": [],
        "test_accuracy": [],
        "epoch_times": [],
    }

    total_batches = len(trainloader)
    total_start = time.time()

    for epoch in range(epochs):
        epoch_start = time.time()

        # ─── Training Phase ───
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        print(f"\n{C.BOLD}{C.BLUE}  ┌─ Epoch {epoch + 1}/{epochs} {'─' * 42}┐{C.RESET}")

        for batch_idx, (inputs, labels) in enumerate(trainloader, 1):
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            # Progress bar every 50 batches
            if batch_idx % 50 == 0 or batch_idx == total_batches:
                elapsed = time.time() - epoch_start
                batches_per_sec = batch_idx / elapsed
                eta = (total_batches - batch_idx) / batches_per_sec if batches_per_sec > 0 else 0

                pct = batch_idx / total_batches
                bar_len = 30
                filled = int(bar_len * pct)
                bar = '█' * filled + '░' * (bar_len - filled)

                avg_loss = running_loss / batch_idx
                acc = 100.0 * correct / total

                sys.stdout.write(
                    f"\r  │ {C.CYAN}{bar}{C.RESET} {pct * 100:5.1f}% "
                    f"│ Loss: {C.YELLOW}{avg_loss:.4f}{C.RESET} "
                    f"│ Acc: {C.GREEN}{acc:5.1f}%{C.RESET} "
                    f"│ ETA: {format_time(eta)} "
                )
                sys.stdout.flush()

        epoch_time = time.time() - epoch_start
        train_loss = running_loss / total_batches
        train_acc = 100.0 * correct / total

        print()  # New line after progress bar

        # ─── Evaluation Phase ───
        model.eval()
        test_correct = 0
        test_total = 0

        with torch.no_grad():
            for inputs, labels in testloader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = outputs.max(1)
                test_total += labels.size(0)
                test_correct += predicted.eq(labels).sum().item()

        test_acc = 100.0 * test_correct / test_total

        print(f"  │")
        print(f"  │  {C.DIM}Train Loss:{C.RESET}  {train_loss:.4f}")
        print(f"  │  {C.DIM}Train Acc:{C.RESET}   {C.GREEN}{train_acc:.2f}%{C.RESET}")
        print(f"  │  {C.DIM}Test Acc:{C.RESET}    {C.GREEN}{test_acc:.2f}%{C.RESET}")
        print(f"  │  {C.DIM}Epoch Time:{C.RESET}  {C.YELLOW}{format_time(epoch_time)}{C.RESET}")

        total_elapsed = time.time() - total_start
        remaining_epochs = epochs - (epoch + 1)
        avg_epoch_time = total_elapsed / (epoch + 1)
        estimated_remaining = avg_epoch_time * remaining_epochs

        print(f"  │  {C.DIM}Total Time:{C.RESET}  {format_time(total_elapsed)} "
              f"{C.DIM}(~{format_time(estimated_remaining)} remaining){C.RESET}")
        print(f"  └{'─' * 56}┘")

        # Record history
        history["epochs"].append(epoch + 1)
        history["train_loss"].append(round(train_loss, 6))
        history["train_accuracy"].append(round(train_acc, 4))
        history["test_accuracy"].append(round(test_acc, 4))
        history["epoch_times"].append(round(epoch_time, 2))

        scheduler.step()

    total_time = time.time() - total_start
    history["total_time_seconds"] = round(total_time, 2)

    return history


# ═══════════════════════════════════════════════════════════════
# SAVE RESULTS
# ═══════════════════════════════════════════════════════════════
def save_results(model, history, device):
    """Save model, training history, and summary."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save model weights
    model_path = os.path.join(OUTPUT_DIR, "trained_model.pth")
    torch.save(model.state_dict(), model_path)

    # Save training history
    results = {
        "model_name": "DeepCNN_VGG_Style",
        "dataset": "CIFAR-10",
        "total_parameters": count_parameters(model),
        "device": str(device),
        "system": {
            "os": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "pytorch": torch.__version__,
        },
        "hyperparameters": {
            "epochs": EPOCHS,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "optimizer": "Adam",
            "scheduler": "StepLR(step=3, gamma=0.1)",
        },
        "training_history": history,
        "final_train_accuracy": history["train_accuracy"][-1],
        "final_test_accuracy": history["test_accuracy"][-1],
        "final_loss": history["train_loss"][-1],
        "total_training_time_seconds": history["total_time_seconds"],
    }

    results_path = os.path.join(OUTPUT_DIR, "training_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  {C.GREEN}✓{C.RESET} Model saved to:   {model_path}")
    print(f"  {C.GREEN}✓{C.RESET} Results saved to:  {results_path}")

    return results


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    print_banner()
    device = print_system_info()

    # ─── Step 1: Load Dataset ───
    print(f"{C.BOLD}  [1/4] LOADING DATASET (CIFAR-10 — 60,000 images){C.RESET}")
    print(f"  {'─' * 50}")

    transform_train = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"  Downloading/loading CIFAR-10 dataset...")
    trainset = torchvision.datasets.CIFAR10(
        root=DATA_DIR, train=True, download=True, transform=transform_train
    )
    testset = torchvision.datasets.CIFAR10(
        root=DATA_DIR, train=False, download=True, transform=transform_test
    )

    trainloader = torch.utils.data.DataLoader(
        trainset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS
    )
    testloader = torch.utils.data.DataLoader(
        testset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS
    )

    print(f"  {C.GREEN}✓{C.RESET} Training samples: {len(trainset):,}")
    print(f"  {C.GREEN}✓{C.RESET} Test samples:     {len(testset):,}")
    print(f"  {C.GREEN}✓{C.RESET} Batch size:       {BATCH_SIZE}")
    print(f"  {C.GREEN}✓{C.RESET} Batches/epoch:    {len(trainloader)}")

    # ─── Step 2: Initialize Model ───
    print(f"\n{C.BOLD}  [2/4] INITIALIZING NEURAL NETWORK{C.RESET}")
    print(f"  {'─' * 50}")

    model = DeepCNN(num_classes=10).to(device)
    total_params = count_parameters(model)

    print(f"  {C.GREEN}✓{C.RESET} Architecture:     VGG-style Deep CNN")
    print(f"  {C.GREEN}✓{C.RESET} Conv blocks:      3 (with BatchNorm)")
    print(f"  {C.GREEN}✓{C.RESET} FC layers:        2 (with Dropout)")
    print(f"  {C.GREEN}✓{C.RESET} Parameters:       {C.YELLOW}{total_params:,}{C.RESET}")
    print(f"  {C.GREEN}✓{C.RESET} Optimizer:        Adam (lr={LEARNING_RATE})")

    # ─── Step 3: Train ───
    print(f"\n{C.BOLD}  [3/4] TRAINING ({EPOCHS} EPOCHS){C.RESET}")
    print(f"  {'─' * 50}")
    print(f"  {C.YELLOW}⚠  This will take several minutes on CPU...{C.RESET}")
    print(f"  {C.DIM}  (On Epochly GPU this takes only seconds){C.RESET}")

    history = train(model, device, trainloader, testloader, EPOCHS)

    # ─── Step 4: Save Results ───
    print(f"\n{C.BOLD}  [4/4] SAVING RESULTS{C.RESET}")
    print(f"  {'─' * 50}")

    results = save_results(model, history, device)

    # ─── Final Summary ───
    total_time = history["total_time_seconds"]

    print(f"\n\n{C.BOLD}{C.CYAN}")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║                                                        ║")
    print("  ║              🏁  TRAINING COMPLETE!                     ║")
    print("  ║                                                        ║")
    print(f"  ║   Total Time:  {format_time(total_time):>10}                           ║")
    print(f"  ║   Final Loss:  {results['final_loss']:>10.4f}                           ║")
    print(f"  ║   Train Acc:   {results['final_train_accuracy']:>9.2f}%                           ║")
    print(f"  ║   Test Acc:    {results['final_test_accuracy']:>9.2f}%                           ║")
    print(f"  ║   Parameters:  {total_params:>10,}                           ║")
    print("  ║                                                        ║")
    print("  ╠══════════════════════════════════════════════════════════╣")
    print("  ║                                                        ║")
    print(f"  ║   ⏱️  It took {C.YELLOW}{format_time(total_time)}{C.CYAN} on this local CPU.            ║")
    print("  ║                                                        ║")
    print("  ║   🚀 Upload this SAME script to Epochly and watch      ║")
    print("  ║      it finish in seconds on GPU!                      ║")
    print("  ║                                                        ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}\n")


if __name__ == "__main__":
    main()
