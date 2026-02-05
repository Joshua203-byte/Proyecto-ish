# ML Model Simulation - Generates realistic output files
# This script simulates training an ML model and generates multiple output files
import time
import random
import os
import json

print("=" * 60)
print("ML MODEL SIMULATION - FULL OUTPUT")
print("=" * 60)

output_dir = "/workspace/output"
os.makedirs(output_dir, exist_ok=True)

# Phase 1: Training
print("\n[1/4] Training model...")
epochs = 10
for epoch in range(epochs):
    loss = 2.0 - (epoch * 0.18) + random.uniform(-0.05, 0.05)
    accuracy = 0.5 + (epoch * 0.048) + random.uniform(-0.02, 0.02)
    print(f"  Epoch {epoch+1:2d}/{epochs} | Loss: {loss:.4f} | Acc: {accuracy:.4f}")
    time.sleep(3)

# Phase 2: Generate config file (like adapter_config.json)
print("\n[2/4] Saving model configuration...")
config = {
    "model_type": "lora_adapter",
    "base_model": "gpt2",
    "r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj"],
    "task_type": "CAUSAL_LM",
    "inference_mode": False,
    "fan_in_fan_out": False,
    "bias": "none"
}
with open(f"{output_dir}/adapter_config.json", "w") as f:
    json.dump(config, f, indent=2)
print("  ✓ adapter_config.json saved")

# Phase 3: Generate fake model weights (binary file)
print("\n[3/4] Saving model weights...")
# Create a fake binary file (simulating safetensors)
fake_weights = bytes([random.randint(0, 255) for _ in range(500000)])
with open(f"{output_dir}/model_weights.bin", "wb") as f:
    f.write(fake_weights)
print("  ✓ model_weights.bin saved (500KB)")

# Phase 4: Generate tokenizer config
tokenizer_config = {
    "model_max_length": 1024,
    "padding_side": "right",
    "truncation_side": "right",
    "clean_up_tokenization_spaces": True,
    "tokenizer_class": "GPT2Tokenizer"
}
with open(f"{output_dir}/tokenizer_config.json", "w") as f:
    json.dump(tokenizer_config, f, indent=2)
print("  ✓ tokenizer_config.json saved")

# Phase 5: Generate training logs CSV
print("\n[4/4] Saving training logs...")
with open(f"{output_dir}/training_logs.csv", "w") as f:
    f.write("epoch,loss,accuracy,learning_rate,time_seconds\n")
    for epoch in range(epochs):
        loss = 2.0 - (epoch * 0.18) + random.uniform(-0.05, 0.05)
        acc = 0.5 + (epoch * 0.048) + random.uniform(-0.02, 0.02)
        lr = 0.0001 * (0.9 ** epoch)
        time_s = random.randint(3, 5)
        f.write(f"{epoch+1},{loss:.6f},{acc:.6f},{lr:.8f},{time_s}\n")
print("  ✓ training_logs.csv saved")

# Generate README
with open(f"{output_dir}/README.md", "w") as f:
    f.write("# Model Training Results\n\n")
    f.write(f"## Summary\n")
    f.write(f"- **Epochs**: {epochs}\n")
    f.write(f"- **Final Loss**: {loss:.6f}\n")
    f.write(f"- **Final Accuracy**: {accuracy:.6f}\n\n")
    f.write("## Files\n")
    f.write("- `adapter_config.json` - Model configuration\n")
    f.write("- `model_weights.bin` - Trained weights\n")
    f.write("- `tokenizer_config.json` - Tokenizer settings\n")
    f.write("- `training_logs.csv` - Training history\n")
print("  ✓ README.md saved")

# Generate metrics JSON
metrics = {
    "final_loss": round(loss, 6),
    "final_accuracy": round(accuracy, 6),
    "total_epochs": epochs,
    "best_epoch": random.randint(7, 10),
    "training_time_seconds": epochs * 4,
    "model_parameters": random.randint(10_000_000, 50_000_000),
    "memory_used_mb": random.randint(500, 2000)
}
with open(f"{output_dir}/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
print("  ✓ metrics.json saved")

print("\n" + "=" * 60)
print("TRAINING COMPLETE!")
print(f"Generated 6 output files in /workspace/output/")
print("=" * 60)
