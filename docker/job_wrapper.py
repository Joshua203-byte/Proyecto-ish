#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
Home-GPU-Cloud Job Wrapper
═══════════════════════════════════════════════════════════════════════════════

This script is the ENTRYPOINT for all user containers. It provides:

1. SIGNAL HANDLING (Graceful Shutdown)
   - Captures SIGTERM (sent when credits run out)
   - Propagates signal to user script
   - Allows grace period for cleanup

2. UNBUFFERED I/O
   - Forces immediate log output
   - User sees logs in real-time on web UI

3. ERROR HANDLING
   - Captures exceptions from user code
   - Formats errors as JSON for the system
   - Distinguishes code errors from infra errors

4. SUBPROCESS MONITORING
   - Runs user script via subprocess.Popen
   - Streams stdout/stderr in real-time
   - Captures exit code

Usage:
    python job_wrapper.py train.py
    python job_wrapper.py train.py --epochs 10 --lr 0.001

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import signal
import argparse
import subprocess
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, List


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Grace period (seconds) after SIGTERM before SIGKILL
GRACE_PERIOD_SECONDS = 10

# Working directories
INPUT_DIR = Path("/workspace/input")
OUTPUT_DIR = Path("/workspace/output")

# Status file for the billing system
STATUS_FILE = OUTPUT_DIR / ".job_status.json"


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════════════════

# The user's subprocess
user_process: Optional[subprocess.Popen] = None

# Flag to track if we received a termination signal
termination_requested = False

# Start time for runtime tracking
start_time: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def log(level: str, message: str) -> None:
    """Print a timestamped log message with immediate flush."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level.upper()}] {message}", flush=True)


def log_info(message: str) -> None:
    log("INFO", message)


def log_warn(message: str) -> None:
    log("WARN", message)


def log_error(message: str) -> None:
    log("ERROR", message)


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

def write_status(
    status: str,
    exit_code: Optional[int] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    traceback_str: Optional[str] = None
) -> None:
    """
    Write job status to JSON file for the system to read.
    
    Status values:
    - "running": Job is executing
    - "completed": Job finished successfully (exit_code = 0)
    - "failed": Job finished with error (exit_code != 0)
    - "terminated": Job was killed (SIGTERM from billing)
    - "error": Wrapper itself encountered an error
    """
    runtime_seconds = 0
    if start_time:
        runtime_seconds = int((datetime.now() - start_time).total_seconds())
    
    status_data = {
        "status": status,
        "exit_code": exit_code,
        "runtime_seconds": runtime_seconds,
        "timestamp": datetime.now().isoformat(),
        "error": None
    }
    
    if error_type or error_message:
        status_data["error"] = {
            "type": error_type,
            "message": error_message,
            "traceback": traceback_str
        }
    
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        log_error(f"Failed to write status file: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL HANDLING (Graceful Shutdown)
# ═══════════════════════════════════════════════════════════════════════════════

def handle_sigterm(signum: int, frame) -> None:
    """
    Handle SIGTERM signal (sent when credits run out).
    
    This is the "Kill Switch" - we need to:
    1. Log the termination
    2. Forward SIGTERM to the user process
    3. Give it GRACE_PERIOD_SECONDS to cleanup
    4. Force kill if it doesn't exit
    """
    global termination_requested
    termination_requested = True
    
    log_warn("=" * 60)
    log_warn("TERMINATION SIGNAL RECEIVED")
    log_warn("Reason: Credits exhausted or external stop request")
    log_warn(f"Grace period: {GRACE_PERIOD_SECONDS} seconds")
    log_warn("=" * 60)
    
    if user_process and user_process.poll() is None:
        log_info("Forwarding SIGTERM to user process...")
        user_process.terminate()
        
        # Start a timer for forced kill
        def force_kill():
            if user_process and user_process.poll() is None:
                log_warn("Grace period expired. Forcing termination (SIGKILL)...")
                user_process.kill()
        
        timer = threading.Timer(GRACE_PERIOD_SECONDS, force_kill)
        timer.start()
    
    write_status("terminated", exit_code=-15, error_message="Job terminated: credits exhausted")


def handle_sigint(signum: int, frame) -> None:
    """Handle SIGINT (Ctrl+C) - treat same as SIGTERM."""
    handle_sigterm(signum, frame)


# Register signal handlers
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigint)


# ═══════════════════════════════════════════════════════════════════════════════
# SUBPROCESS EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def stream_output(pipe, prefix: str = "") -> None:
    """Stream output from a pipe line by line with immediate flush."""
    try:
        for line in iter(pipe.readline, ''):
            if line:
                # Print with flush for real-time output
                print(f"{prefix}{line}", end='', flush=True)
    except Exception as e:
        log_error(f"Error streaming output: {e}")
    finally:
        pipe.close()


def run_user_script(script_path: Path, extra_args: List[str]) -> int:
    """
    Execute the user's Python script as a subprocess.
    
    Returns:
        exit_code: 0 for success, non-zero for failure
    """
    global user_process
    
    # Build command
    cmd = [sys.executable, "-u", str(script_path)] + extra_args
    
    log_info(f"Executing: {' '.join(cmd)}")
    log_info(f"Working directory: {os.getcwd()}")
    log_info("-" * 60)
    
    # Start subprocess with unbuffered output
    user_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        bufsize=1,  # Line buffered
        universal_newlines=True,
        env={
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "UTF-8",
        },
        cwd=INPUT_DIR  # Run from input directory
    )
    
    # Stream output in real-time
    stream_output(user_process.stdout)
    
    # Wait for process to complete
    exit_code = user_process.wait()
    
    log_info("-" * 60)
    log_info(f"Process exited with code: {exit_code}")
    
    return exit_code


# ═══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def verify_gpu() -> bool:
    """Check if CUDA is available and log GPU info."""
    try:
        import torch
        
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            log_info(f"CUDA available: {device_count} GPU(s) detected")
            
            for i in range(device_count):
                name = torch.cuda.get_device_name(i)
                memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                log_info(f"  GPU {i}: {name} ({memory:.1f} GB)")
            
            return True
        else:
            log_warn("CUDA not available - running in CPU mode")
            return False
            
    except ImportError:
        log_warn("PyTorch not installed - cannot verify GPU")
        return False
    except Exception as e:
        log_error(f"Error checking GPU: {e}")
        return False


def print_environment_info() -> None:
    """Print environment information for debugging."""
    log_info("=" * 60)
    log_info("HOME-GPU-CLOUD JOB WRAPPER")
    log_info("=" * 60)
    log_info(f"Python: {sys.version}")
    log_info(f"Job ID: {os.environ.get('JOB_ID', 'unknown')}")
    log_info(f"Input dir: {INPUT_DIR}")
    log_info(f"Output dir: {OUTPUT_DIR}")
    verify_gpu()
    log_info("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    """Main entry point for the job wrapper."""
    global start_time
    start_time = datetime.now()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Home-GPU-Cloud Job Wrapper - Execute user scripts safely",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python job_wrapper.py train.py
    python job_wrapper.py train.py --epochs 10 --batch-size 32
    python job_wrapper.py train.py --config config.yaml
        """
    )
    parser.add_argument(
        "script",
        nargs="?",
        help="Python script to execute (relative to /workspace/input)"
    )
    parser.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the user script"
    )
    
    args = parser.parse_args()
    
    # Print environment info
    print_environment_info()
    
    # Check if script was provided
    if not args.script:
        log_error("No script specified!")
        log_info("Usage: python job_wrapper.py <script.py> [args...]")
        write_status("error", exit_code=1, error_type="ArgumentError", 
                     error_message="No script specified")
        return 1
    
    # Resolve script path
    script_path = INPUT_DIR / args.script
    
    if not script_path.exists():
        log_error(f"Script not found: {script_path}")
        log_info(f"Available files in {INPUT_DIR}:")
        for f in INPUT_DIR.iterdir():
            log_info(f"  - {f.name}")
        write_status("error", exit_code=1, error_type="FileNotFoundError",
                     error_message=f"Script not found: {args.script}")
        return 1
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write initial status
    write_status("running")
    
    try:
        # Execute user script
        exit_code = run_user_script(script_path, args.script_args or [])
        
        # Check if we were terminated
        if termination_requested:
            log_warn("Job was terminated before completion")
            write_status("terminated", exit_code=-15)
            return -15
        
        # Check exit code
        if exit_code == 0:
            log_info("=" * 60)
            log_info("JOB COMPLETED SUCCESSFULLY")
            log_info("=" * 60)
            write_status("completed", exit_code=0)
        else:
            log_error("=" * 60)
            log_error(f"JOB FAILED (exit code: {exit_code})")
            log_error("=" * 60)
            write_status("failed", exit_code=exit_code, 
                        error_type="ScriptError",
                        error_message=f"Script exited with code {exit_code}")
        
        return exit_code
        
    except Exception as e:
        # Unexpected error in wrapper
        tb = traceback.format_exc()
        log_error("=" * 60)
        log_error("WRAPPER ERROR (not user code)")
        log_error(str(e))
        log_error(tb)
        log_error("=" * 60)
        
        write_status(
            "error",
            exit_code=255,
            error_type=type(e).__name__,
            error_message=str(e),
            traceback_str=tb
        )
        
        return 255


if __name__ == "__main__":
    sys.exit(main())
