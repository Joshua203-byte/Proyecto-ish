#!/usr/bin/env python3
"""
🚀 SYSTEM STRESS TEST - 30 MINUTE WORKLOAD
This script is designed to push the GPU and CPU to their limits for approximately 30 minutes.
It trains a ResNet50 model on high-resolution synthetic data and performs periodic heavy disk I/O.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
import time
import os
import json
from pathlib import Path

# --- CONFIGURATION ---
BATCH_SIZE = 64          # Adjust based on VRAM (64 is heavy for 224x224)
IMAGE_SIZE = 224         # Standard ResNet size
EPOCHS = 40              # Aiming for ~30-40 minutes on high-end GPUs
STEPS_PER_EPOCH = 250    # Total 10,000 steps
CHECKPOINT_INTERVAL = 5  # Save a heavy model every 5 epochs
# ---------------------

def print_header(text):
    print("\n" + "="*60)
    print(f"🔥 {text}")
    print("="*60)

print_header("INICIANDO PRUEBA DE ESTRÉS (30 MINUTOS)")

# 1. Check Hardware
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"📍 Dispositivo: {device}")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    total_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"📍 GPU: {gpu_name}")
    print(f"📍 VRAM Total: {total_mem:.2f} GB")
else:
    print("⚠️ ADVERTENCIA: No se detectó GPU. La prueba correrá en CPU (será MUCHO más lenta).")

# 2. Initialize Model (ResNet50 is heavy enough)
print("\n📦 Cargando modelo ResNet50...")
model = models.resnet50(weights=None).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 3. Stress Loop
print_header("EJECUTANDO CARGA DE TRABAJO")
print(f"Configuración: {EPOCHS} épocas, {STEPS_PER_EPOCH} pasos por época.")
print(f"Tamaño de batch: {BATCH_SIZE}, Resolución: {IMAGE_SIZE}x{IMAGE_SIZE}")

start_time = time.time()
epoch_times = []

try:
    for epoch in range(EPOCHS):
        epoch_start = time.time()
        model.train()
        running_loss = 0.0
        
        for step in range(STEPS_PER_EPOCH):
            # Generate synthetic heavy data
            inputs = torch.randn(BATCH_SIZE, 3, IMAGE_SIZE, IMAGE_SIZE).to(device)
            labels = torch.randint(0, 1000, (BATCH_SIZE,)).to(device)
            
            # Forward + Backward + Optimize
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            if (step + 1) % 50 == 0:
                elapsed = time.time() - start_time
                print(f"   [Época {epoch+1}/{EPOCHS}] Paso {step+1}/{STEPS_PER_EPOCH} | Loss: {loss.item():.4f} | Tiempo transcurrido: {elapsed/60:.2f} min")

        # Epoch stats
        epoch_duration = time.time() - epoch_start
        epoch_times.append(epoch_duration)
        
        # 4. Disk I/O Stress (Save Checkpoint)
        if (epoch + 1) % CHECKPOINT_INTERVAL == 0:
            print(f"💾 Guardando checkpoint pesado (Estrés de Disco)...")
            ckpt_path = f"stress_test_epoch_{epoch+1}.pth"
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
            }, ckpt_path)
            # Simulate some wait for I/O
            time.sleep(1)
            # Remove to avoid filling up disk too much, but keep the last one
            if epoch + 1 < EPOCHS:
                if os.path.exists(ckpt_path):
                    os.remove(ckpt_path)

    total_duration = time.time() - start_time
    print_header("PRUEBA COMPLETADA EXITOSAMENTE")
    print(f"⏱️ Tiempo Total: {total_duration/60:.2f} minutos")
    print(f"📊 Promedio por Época: {sum(epoch_times)/len(epoch_times):.2f} segundos")
    
    # Save final report
    report = {
        "status": "success",
        "total_time_min": total_duration / 60,
        "device": str(device),
        "gpu": gpu_name if torch.cuda.is_available() else "N/A",
        "epochs_completed": EPOCHS,
        "vram_peak_gb": torch.cuda.max_memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
    }
    
    with open("stress_test_report.json", "w") as f:
        json.dump(report, f, indent=4)
    print(f"📄 Reporte guardado en: stress_test_report.json")

except Exception as e:
    print_header("ERROR DURANTE LA PRUEBA")
    print(f"❌ Detalle: {str(e)}")
    with open("stress_test_error.json", "w") as f:
        json.dump({"status": "failed", "error": str(e)}, f, indent=4)
    raise e
