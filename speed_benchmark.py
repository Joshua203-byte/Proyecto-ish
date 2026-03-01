import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import time
import os
import warnings

# Suppress CUDA compatibility warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, message=".*NVIDIA.*not compatible.*")

def main():
    print("=" * 60)
    print("🚀 AI TRAINING SPEED BENCHMARK (Local CPU vs Epochly GPU)")
    print("=" * 60)

    # 1. Smart device selection - auto-detects if GPU actually works
    device = torch.device("cpu")  # Default to CPU
    if torch.cuda.is_available():
        try:
            # Test if the GPU actually works by doing a small operation
            test_tensor = torch.zeros(1).cuda()
            _ = test_tensor + 1
            device = torch.device("cuda")
        except RuntimeError:
            # GPU detected but not compatible (e.g. local DGX Spark with wrong PyTorch)
            pass

    print(f"[*] Target device detected: {device.type.upper()}")
    if device.type == "cuda":
        print(f"    - GPU Model: {torch.cuda.get_device_name(0)}")
        print("    - Expect this to be blazingly fast!")
    else:
        print("    - Running on CPU. Grab a coffee, this will take a while...")
    
    # 2. Download and load dataset (CIFAR-10: 60,000 images, 10 classes)
    print("\n[*] Preparing the dataset (CIFAR-10)...")
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    # The dataset downloads automatically the first time you run it
    os.makedirs("./data", exist_ok=True)
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                            download=True, transform=transform)
    
    batch_size = 128
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size,
                                              shuffle=True, num_workers=2)
    
    # 3. Define a Deep Convolutional Neural Network
    print("\n[*] Initializing Deep Neural Network (VGG-style)...")
    class SimpleVGG(nn.Module):
        def __init__(self):
            super(SimpleVGG, self).__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 64, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
                
                nn.Conv2d(64, 128, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
                
                nn.Conv2d(128, 256, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=2, stride=2),
            )
            self.classifier = nn.Sequential(
                nn.Linear(256 * 4 * 4, 1024),
                nn.ReLU(inplace=True),
                nn.Dropout(),
                nn.Linear(1024, 10)
            )

        def forward(self, x):
            x = self.features(x)
            x = x.view(x.size(0), -1)
            x = self.classifier(x)
            return x
            
    model = SimpleVGG().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 4. Training Loop
    epochs = 3 # 3 epochs is enough to show a massive difference in time
    print(f"\n[*] Starting training for {epochs} epochs...")
    
    total_start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        model.train()
        running_loss = 0.0
        
        for i, (inputs, labels) in enumerate(trainloader, 0):
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            # Print every 100 batches to show progress visually
            if i % 100 == 99:
                print(f"    - [Epoch {epoch+1}, Batch {i+1}] Loss: {running_loss / 100:.3f}")
                running_loss = 0.0
                
        epoch_time = time.time() - epoch_start
        print(f"    => Epoch {epoch+1} completed in {epoch_time:.2f} seconds")
        
    total_time = time.time() - total_start_time
    
    print("\n" + "=" * 60)
    print("🎉 TRAINING COMPLETE!")
    print(f"Total time taken: {total_time:.2f} seconds")
    
    # Print dynamic message for the video ending
    if device.type == 'cpu':
        print("\n💡 TIMELINE COMPARISON:")
        print(f"It took {total_time:.2f}s on this local CPU.")
        print("Now, run this exact same script on Epochly to see the magic! 🚀")
    else:
        print("\n💡 TIMELINE COMPARISON:")
        print(f"Wow! Only {total_time:.2f}s on Epochly GPU! 🔥")
        print("Compare this with the agonizing wait on a regular laptop CPU.")
    print("=" * 60)

if __name__ == "__main__":
    main()
