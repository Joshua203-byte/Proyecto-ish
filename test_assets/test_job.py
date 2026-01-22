import os
import time
import sys
import json
import csv

def run_test():
    print("--- GPU Cloud Test Job Starting (LLM Simulation Mode) ---")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}")
    
    # Check for Job ID in environment
    job_id = os.environ.get('JOB_ID', 'unknown_job')
    print(f"Job ID: {job_id}")
    
    # Simulate training process
    print("🚀 Initializing model: Llama-3-70b-Instruct...")
    time.sleep(2)
    print("📦 Loading LoRA adapters...")
    time.sleep(1)
    
    epochs = 5
    print(f"🔄 Starting Fine-Tuning ({epochs} epochs)...")
    
    # Simulate training progress
    for i in range(1, epochs + 1):
        loss = 2.5 - (i * 0.4) + (0.1 * (i % 2)) # Fake loss curve
        print(f"Epoch {i}/{epochs} - loss: {loss:.4f} - accuracy: {0.6 + (i*0.05):.4f}")
        time.sleep(1.5)
        
    print("✅ Training completed successfully!")
    
    # Create Output Directory structure
    output_dir = "/workspace/output"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"💾 Saving model artifacts to {output_dir}...")
    
    # 1. Create Dummy Adapter (The "Gold")
    print("   -> adapter_model.safetensors (150MB dummy)")
    with open(f"{output_dir}/adapter_model.safetensors", "wb") as f:
        # Write 10MB of dummy zeros to simulate weight file
        f.write(b'\0' * 1024 * 1024 * 10) 
        
    # 2. Adapter Config
    print("   -> adapter_config.json")
    config = {
        "base_model_name_or_path": "meta-llama/Llama-2-7b-hf",
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "r": 8,
        "bias": "none",
        "task_type": "CAUSAL_LM"
    }
    with open(f"{output_dir}/adapter_config.json", "w") as f:
        json.dump(config, f, indent=2)
        
    # 3. Tokenizer
    print("   -> tokenizer.json")
    with open(f"{output_dir}/tokenizer.json", "w") as f:
        json.dump({"vocab_size": 32000, "model_type": "llama"}, f)
        
    # 4. Training Logs
    print("   -> training_logs.csv")
    with open(f"{output_dir}/training_logs.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "loss", "accuracy", "learning_rate"])
        for i in range(1, epochs + 1):
             writer.writerow([i, 2.5 - (i * 0.4), 0.6 + (i*0.05), 2e-4])

    # 5. README
    print("   -> README.md")
    with open(f"{output_dir}/README.md", "w") as f:
        f.write(f"# Fine-Tuned Model: Job {job_id}\n")
        f.write("This model was fine-tuned using the Home GPU Cloud infrastructure.\n")
        f.write("\n## Usage\n```python\nfrom peft import PeftModel, PeftConfig\nfrom transformers import AutoModelForCausalLM\n\nconfig = PeftConfig.from_pretrained('path/to/adapter')\nmodel = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)\nmodel = PeftModel.from_pretrained(model, 'path/to/adapter')\n```")

    print(f"✨ All artifacts saved. Ready for download.")
    print("--- GPU Cloud Test Job Finished ---")

if __name__ == "__main__":
    run_test()
