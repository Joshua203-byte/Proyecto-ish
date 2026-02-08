"""
Prueba 2: Entrenamiento de Transformer desde cero
Modelo de lenguaje similar a GPT con datos sintéticos
"""
import torch
import torch.nn as nn
import torch.optim as optim
import time
import argparse
import math

print("=" * 60)
print("PRUEBA 2: Transformer Language Model Training")
print("=" * 60)

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--epochs', type=int, default=3, help='Number of epochs')
parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
parser.add_argument('--seq-len', type=int, default=512, help='Sequence length')
parser.add_argument('--d-model', type=int, default=512, help='Model dimension')
parser.add_argument('--n-heads', type=int, default=8, help='Number of attention heads')
parser.add_argument('--n-layers', type=int, default=6, help='Number of transformer layers')
args = parser.parse_args()

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n✓ Device: {device}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")

# Transformer Model
class TransformerLM(nn.Module):
    def __init__(self, vocab_size, d_model, n_heads, n_layers, seq_len):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = nn.Embedding(seq_len, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=d_model*4,
            dropout=0.1, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.fc_out = nn.Linear(d_model, vocab_size)
        self.d_model = d_model
        
    def forward(self, x):
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device).unsqueeze(0)
        x = self.embedding(x) * math.sqrt(self.d_model) + self.pos_encoding(positions)
        
        # Causal mask
        mask = nn.Transformer.generate_square_subsequent_mask(seq_len).to(x.device)
        x = self.transformer(x, mask=mask, is_causal=True)
        return self.fc_out(x)

# Create model
print(f"\n[1/4] Building Transformer...")
print(f"  d_model: {args.d_model}")
print(f"  n_heads: {args.n_heads}")
print(f"  n_layers: {args.n_layers}")
print(f"  seq_len: {args.seq_len}")

vocab_size = 50000
model = TransformerLM(vocab_size, args.d_model, args.n_heads, args.n_layers, args.seq_len).to(device)
params = sum(p.numel() for p in model.parameters())
print(f"  Parameters: {params:,} ({params/1e6:.1f}M)")

# Synthetic data
print(f"\n[2/4] Creating synthetic text data...")
class SyntheticTextDataset(torch.utils.data.Dataset):
    def __init__(self, vocab_size, seq_len, num_samples=5000):
        self.vocab_size = vocab_size
        self.seq_len = seq_len
        self.num_samples = num_samples
    def __len__(self):
        return self.num_samples
    def __getitem__(self, idx):
        tokens = torch.randint(0, self.vocab_size, (self.seq_len + 1,))
        return tokens[:-1], tokens[1:]  # input, target

dataset = SyntheticTextDataset(vocab_size, args.seq_len)
loader = torch.utils.data.DataLoader(dataset, batch_size=args.batch_size, 
                                      shuffle=True, num_workers=2)

# Training
print(f"\n[3/4] Setting up training...")
criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
scaler = torch.amp.GradScaler('cuda', enabled=torch.cuda.is_available())

print(f"\n[4/4] Training for {args.epochs} epochs...")
print("-" * 60)

total_start = time.time()
for epoch in range(args.epochs):
    model.train()
    epoch_loss = 0
    epoch_start = time.time()
    
    for batch_idx, (inputs, targets) in enumerate(loader):
        inputs, targets = inputs.to(device), targets.to(device)
        
        optimizer.zero_grad()
        
        with torch.amp.autocast('cuda', enabled=torch.cuda.is_available()):
            outputs = model(inputs)
            loss = criterion(outputs.view(-1, vocab_size), targets.view(-1))
        
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        epoch_loss += loss.item()
        
        if (batch_idx + 1) % 10 == 0:
            tokens_per_sec = (batch_idx + 1) * args.batch_size * args.seq_len / (time.time() - epoch_start)
            print(f"  Epoch {epoch+1} | Batch {batch_idx+1}/{len(loader)} | "
                  f"Loss: {loss.item():.4f} | Speed: {tokens_per_sec/1000:.1f}K tok/s")
    
    epoch_time = time.time() - epoch_start
    perplexity = math.exp(epoch_loss / len(loader))
    print(f"  → Epoch {epoch+1}: {epoch_time:.2f}s | Loss: {epoch_loss/len(loader):.4f} | PPL: {perplexity:.2f}")

total_time = time.time() - total_start

# Results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Model: Transformer LM ({params/1e6:.1f}M params)")
print(f"Device: {device}")
print(f"Total time: {total_time:.2f} seconds")
print(f"Tokens/second: {args.epochs * len(dataset) * args.seq_len / total_time / 1000:.1f}K")
print("=" * 60)

# Save
import json, os
os.makedirs("/workspace/output", exist_ok=True)
with open("/workspace/output/results.json", "w") as f:
    json.dump({
        "test": "Transformer LM Training",
        "parameters": params,
        "device": str(device),
        "total_time_seconds": round(total_time, 2)
    }, f, indent=2)
print("\n✓ Results saved")
