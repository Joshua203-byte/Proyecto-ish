import os
import time
import sys

def run_test():
    print("--- GPU Cloud Test Job Starting ---")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}")
    
    # Check for Job ID in environment
    job_id = os.environ.get('JOB_ID', 'unknown_job')
    print(f"Job ID: {job_id}")
    
    # Simulate some "work"
    print("Computing important math...")
    for i in range(1, 6):
        print(f"Progress: {i*20}% done")
        time.sleep(2)
    
    # Check for dataset
    data_path = "/workspace/input/data"
    if os.path.exists(data_path):
        print(f"✅ Dataset found at {data_path}")
        files = os.listdir(data_path)
        print(f"Files in dataset: {files}")
    else:
        print("ℹ️ No dataset provided.")
        
    # Write output
    output_path = "/workspace/output/results.txt"
    print(f"Saving results to {output_path}...")
    with open(output_path, "w") as f:
        f.write(f"Job {job_id} completed successfully!\n")
        f.write(f"Timestamp: {time.ctime()}\n")
        f.write("Status: Production mode verified.\n")
    
    print("--- GPU Cloud Test Job Finished ---")

if __name__ == "__main__":
    run_test()
