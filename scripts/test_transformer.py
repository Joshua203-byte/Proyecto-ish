#!/usr/bin/env python3
"""
Transformer/LLM Inference Test
Tests GPU with transformer-style operations (attention, etc.)
Expected runtime: 3-5 minutes
"""
import torch
import torch.nn as nn
import time
import json
from pathlib import Path

print("=" * 60)
print("🤖 TRANSFORMER INFERENCE TEST")
print("=" * 60)

# Check GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\nDevice: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# Transformer parameters (similar to GPT-2 Medium)
BATCH_SIZE = 8
SEQ_LENGTH = 512
HIDDEN_SIZE = 1024
NUM_HEADS = 16
NUM_LAYERS = 24
VOCAB_SIZE = 50257
NUM_ITERATIONS = 20

print(f"\nConfiguration:")
print(f"  Batch size: {BATCH_SIZE}")
print(f"  Sequence length: {SEQ_LENGTH}")
print(f"  Hidden size: {HIDDEN_SIZE}")
print(f"  Attention heads: {NUM_HEADS}")
print(f"  Layers: {NUM_LAYERS}")

# Create transformer model
print("\n📦 Creating transformer model...")

class SimpleTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(VOCAB_SIZE, HIDDEN_SIZE)
        self.pos_embedding = nn.Embedding(SEQ_LENGTH, HIDDEN_SIZE)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=HIDDEN_SIZE,
            nhead=NUM_HEADS,
            dim_feedforward=HIDDEN_SIZE * 4,
            dropout=0.1,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=NUM_LAYERS)
        self.fc_out = nn.Linear(HIDDEN_SIZE, VOCAB_SIZE)
    
    def forward(self, x):
        positions = torch.arange(x.size(1), device=x.device).unsqueeze(0)
        x = self.embedding(x) + self.pos_embedding(positions)
        x = self.transformer(x)
        x = self.fc_out(x)
        return x

model = SimpleTransformer().to(device)
model.eval()

num_params = sum(p.numel() for p in model.parameters())
print(f"Model parameters: {num_params:,} ({num_params/1e9:.2f}B)")
print(f"GPU Memory after model: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

# Warmup
print("\n🔄 Warming up...")
with torch.no_grad():
    dummy_input = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE, SEQ_LENGTH), device=device)
    for _ in range(3):
        _ = model(dummy_input)
        torch.cuda.synchronize()

# Benchmark inference
print("\n⚡ Running inference benchmark...")
times = []
tokens_processed = 0

with torch.no_grad():
    for i in range(NUM_ITERATIONS):
        input_ids = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE, SEQ_LENGTH), device=device)
        
        start = time.perf_counter()
        output = model(input_ids)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        
        times.append(elapsed)
        tokens_processed += BATCH_SIZE * SEQ_LENGTH
        
        tokens_per_sec = (BATCH_SIZE * SEQ_LENGTH) / elapsed
        print(f"  Iteration {i+1}/{NUM_ITERATIONS} - {elapsed*1000:.1f}ms - {tokens_per_sec:.0f} tokens/sec")

# Results
avg_time = sum(times) / len(times)
total_tokens = BATCH_SIZE * SEQ_LENGTH * NUM_ITERATIONS
tokens_per_sec = total_tokens / sum(times)

print("\n" + "=" * 60)
print("📈 INFERENCE RESULTS")
print("=" * 60)
print(f"Average latency: {avg_time*1000:.2f} ms per batch")
print(f"Throughput: {tokens_per_sec:.0f} tokens/second")
print(f"Total tokens processed: {total_tokens:,}")
print(f"GPU Memory Peak: {torch.cuda.max_memory_allocated() / 1024**3:.2f} GB")

# Save results
results = {
    "test": "transformer_inference",
    "model_params": num_params,
    "batch_size": BATCH_SIZE,
    "seq_length": SEQ_LENGTH,
    "num_layers": NUM_LAYERS,
    "iterations": NUM_ITERATIONS,
    "avg_latency_ms": avg_time * 1000,
    "tokens_per_sec": tokens_per_sec,
    "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
    "memory_peak_gb": torch.cuda.max_memory_allocated() / 1024**3
}

output_path = Path("/tmp/transformer_test_results.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n💾 Results saved to: {output_path}")

print("\n✅ TRANSFORMER TEST COMPLETE!")
