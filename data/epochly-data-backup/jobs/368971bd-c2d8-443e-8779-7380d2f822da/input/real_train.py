import os
import sys
import subprocess
import time
import json
import csv

def install_dependencies():
    print("📦 Installing ML dependencies (this may take a few minutes)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "transformers", "peft", "accelerate", "numpy"])

def train_real_model():
    print("--- GPU Cloud REAL Training Job Starting ---")
    print(f"Working Directory: {os.getcwd()}")
    
    # 1. Install Deps
    try:
        import torch
        import transformers
    except ImportError:
        install_dependencies()
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
        from peft import get_peft_model, LoraConfig, TaskType

    print(f"🔥 Torch Version: {torch.__version__}")
    print(f"🔥 CUDA Available: {torch.cuda.is_available()}")
    
    # 2. Setup Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"⚙️ Using device: {device}")

    # 3. Load Tiny Model (DistilGPT2 is small ~300MB, acceptable for demo)
    model_name = "distilgpt2"
    print(f"⬇️ Downloading model: {model_name}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.to(device)
    
    # 4. Apply LoRA (The "Real" Fine-Tuning tech)
    print("🛠️ Applying LoRA adapters...")
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM, 
        inference_mode=False, 
        r=8, 
        lora_alpha=32, 
        lora_dropout=0.1
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 5. Synthetic Dataset (Medical examples as requested)
    print("📚 Preparing dataset...")
    texts = [
        "Patient exhibits signs of hypertension. Recommended treatment: lisinopril.",
        "Diagnosis: Type 2 Diabetes. Patient requires metformin and lifestyle changes.",
        "Symptoms include fever and cough. Possible influenza. Prescribe rest and fluids.",
        "Acute pain in lower back. MRI recommended to rule out herniated disc.",
        "Patient reports insomnia. Suggest melatonin and sleep hygiene improvements."
    ] * 10  # Duplicate to have enough data for a few steps
    
    # Simple data collator/dataset
    class SimpleDataset(torch.utils.data.Dataset):
        def __init__(self, txt_list, tokenizer):
            self.encodings = [tokenizer(txt, truncation=True, padding="max_length", max_length=64, return_tensors="pt") for txt in txt_list]
        def __len__(self): return len(self.encodings)
        def __getitem__(self, i): 
            item = {key: val[0] for key, val in self.encodings[i].items()}
            item["labels"] = item["input_ids"].clone()
            return item

    dataset = SimpleDataset(texts, tokenizer)
    
    # Use DataLoader to handle batching (adds batch dimension [B, Seq])
    from torch.utils.data import DataLoader
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    # 6. Output Config
    output_dir = "/workspace/output"
    os.makedirs(output_dir, exist_ok=True)

    # 7. Training Loop (Manual loop to show progress or use Trainer)
    # Using Trainer is easier but might require 'accelerate'. Let's do a simple manual loop to be robust.
    print(f"🚀 Starting training on {len(texts)} samples...")
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4)
    
    epochs = 3
    logs = []
    
    for epoch in range(epochs):
        epoch_loss = 0
        for i, batch in enumerate(dataloader):
            # Move batch to device
            batch = {k: v.to(device) for k, v in batch.items()}
            
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            
            epoch_loss += loss.item()
            
        avg_loss = epoch_loss / len(dataset)
        print(f"   Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}")
        logs.append(f"{epoch+1},{avg_loss:.4f}")

    print("✅ Training completed!")

    # 8. Save Artifacts
    print(f"💾 Saving LoRA adapters to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir) # Save tokenizer too

    # 9. Save Logs CSV
    print("   -> training_logs.csv")
    with open(f"{output_dir}/training_logs.csv", "w") as f:
        f.write("epoch,loss\n")
        for log in logs:
            f.write(log + "\n")

    # 10. Save README
    print("   -> README.md")
    with open(f"{output_dir}/README.md", "w") as f:
        f.write(f"# Fine-Tuned DistilGPT2 (Medical Demo)\n")
        f.write(f"This model was REAL-TIME fine-tuned on the Home GPU Cloud.\n")
        f.write(f"- Base Model: distilgpt2\n")
        f.write(f"- Task: Causal LM (Medical Text)\n")
        f.write(f"- Epochs: {epochs}\n")
        f.write(f"- Final Loss: {avg_loss:.4f}\n")
        f.write("\n## How to use\nUse `peft` and `transformers` to load this adapter.")

    print(f"✨ All REAL artifacts saved. Download the ZIP to verify weights!")
    print("--- Job Finished ---")

if __name__ == "__main__":
    train_real_model()
