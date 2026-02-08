"""
Prueba 3: Generación de imágenes con Stable Diffusion
Descarga el modelo de HuggingFace y genera imágenes
"""
import torch
import time
import argparse
import os
import subprocess
import sys

# Install diffusers dependencies explicitly (auto-installer may miss these)
print("Installing Stable Diffusion dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", 
                       "diffusers", "transformers", "accelerate", "safetensors"])
print("✓ Dependencies installed")

print("=" * 60)
print("PRUEBA 3: Stable Diffusion Image Generation")
print("=" * 60)

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--prompt', type=str, default="A beautiful sunset over mountains, digital art, highly detailed", 
                    help='Text prompt for image generation')
parser.add_argument('--num-images', type=int, default=4, help='Number of images to generate')
parser.add_argument('--steps', type=int, default=30, help='Number of inference steps')
parser.add_argument('--guidance', type=float, default=7.5, help='Guidance scale')
args = parser.parse_args()

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n✓ Device: {device}")
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Load model
print("\n[1/3] Loading Stable Diffusion model from HuggingFace...")
print("  (This may take a few minutes on first run)")

from diffusers import StableDiffusionPipeline

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    safety_checker=None  # Disable for speed
)
pipe = pipe.to(device)

# Enable optimizations
if torch.cuda.is_available():
    pipe.enable_attention_slicing()
    try:
        pipe.enable_xformers_memory_efficient_attention()
        print("  ✓ xFormers enabled")
    except:
        print("  ⚠ xFormers not available")

print(f"\n[2/3] Generating {args.num_images} images...")
print(f"  Prompt: {args.prompt}")
print(f"  Steps: {args.steps}")
print(f"  Guidance: {args.guidance}")
print("-" * 60)

# Generate images
os.makedirs("/workspace/output", exist_ok=True)
times = []

for i in range(args.num_images):
    start = time.time()
    
    with torch.amp.autocast('cuda', enabled=torch.cuda.is_available()):
        image = pipe(
            args.prompt,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance
        ).images[0]
    
    gen_time = time.time() - start
    times.append(gen_time)
    
    # Save image
    image_path = f"/workspace/output/image_{i+1}.png"
    image.save(image_path)
    print(f"  Image {i+1}/{args.num_images}: {gen_time:.2f}s → {image_path}")

# Results
avg_time = sum(times) / len(times)
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Device: {device}")
print(f"Images generated: {args.num_images}")
print(f"Average time per image: {avg_time:.2f} seconds")
print(f"Total time: {sum(times):.2f} seconds")
print("=" * 60)

# Save metadata
import json
with open("/workspace/output/results.json", "w") as f:
    json.dump({
        "test": "Stable Diffusion Generation",
        "prompt": args.prompt,
        "num_images": args.num_images,
        "steps": args.steps,
        "device": str(device),
        "avg_time_per_image": round(avg_time, 2),
        "total_time": round(sum(times), 2)
    }, f, indent=2)

print(f"\n✓ {args.num_images} images saved to /workspace/output/")
