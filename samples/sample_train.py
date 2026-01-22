import time
import os
import pandas as pd

def main():
    print("--- GPU Training Simulation Started ---")
    
    # Check for data
    if os.path.exists('data.csv'):
        print("Found dataset: data.csv")
        df = pd.read_csv('data.csv')
        print(f"Dataset shape: {df.shape}")
    else:
        print("No data.csv found, using synthetic data.")

    # Simulate training loop
    epochs = 5
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs}")
        time.sleep(2)  # Simulate workload
        print(f"Loss: {0.5 / (epoch + 1):.4f} | Accuracy: {0.8 + (0.02 * epoch):.4f}")

    print("--- Training Complete ---")
    print("Saving model weights to 'model_output.txt'...")
    with open('model_output.txt', 'w') as f:
        f.write("Model weights saved successfully.")
    
    print("Job finished!")

if __name__ == "__main__":
    main()
