# 🖥️ Local AI Training — CPU Benchmark

This folder contains a **real** AI training program that trains a deep neural network on your local computer using only the CPU.

**Purpose:** Demonstrate that training AI locally is very slow compared to using [Epochly](https://epochly.io)'s GPU infrastructure.

## Quick Start

```bash
# 1. Install dependencies
pip install -r local_training/requirements.txt

# 2. Run training (terminal only)
python3 local_training/train_local.py
```

## What It Does

| Component         | Detail                         |
|-------------------|--------------------------------|
| **Model**         | VGG-style Deep CNN (~3.5M params) |
| **Dataset**       | CIFAR-10 (60,000 images, auto-downloads) |
| **Epochs**        | 5                              |
| **Device**        | CPU only (forced, no GPU)      |
| **Expected Time** | 5–15+ minutes on a typical laptop |

## Output

After training completes, results are saved in `local_training/output/`:

- `trained_model.pth` — Trained model weights
- `training_results.json` — Full metrics (loss, accuracy, timing per epoch)

## For the Video

1. Run `python3 local_training/train_local.py` on your local machine and record the terminal
2. Upload the same script to Epochly → it runs on GPU in **seconds**
3. Compare the two side by side → Epochly is dramatically faster 🚀
