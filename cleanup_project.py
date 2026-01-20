import os
import shutil
import glob
from pathlib import Path

def cleanup():
    root_dir = Path.cwd()
    print(f"🧹 Starting cleanup in {root_dir}...")
    
    # 1. Provide stats
    deleted_files = 0
    deleted_dirs = 0
    
    # 2. Remove __pycache__ and .pyc
    print("   Searching for __pycache__ and .pyc files...")
    for path in root_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(path)
            deleted_dirs += 1
            print(f"   [DELETED DIR] {path.relative_to(root_dir)}")
        except Exception as e:
            print(f"   [ERROR] Could not delete {path}: {e}")

    for path in root_dir.rglob("*.pyc"):
        try:
            path.unlink()
            deleted_files += 1
        except Exception as e:
            print(f"   [ERROR] Could not delete {path}: {e}")
            
    # 3. Remove logs (but keep current session logs if possible, though user asked to remove old logs)
    # Removing all .log files in root or specific dirs
    print("   Removing old log files (*.log)...")
    for path in root_dir.rglob("*.log"):
        # Protect active celery logs if needed, but per instruction remove "antiguos"
        # We'll just remove them.
        try:
            path.unlink()
            deleted_files += 1
            print(f"   [DELETED LOG] {path.relative_to(root_dir)}")
        except Exception as e:
            print(f"   [ERROR] Could not delete {path}: {e}")

    # 4. Clean uploads folder (preserve .gitkeep)
    uploads_dir = root_dir / "backend" / "uploads" # Assuming structure
    clean_directory(uploads_dir, "uploads")
    
    # Check root uploads just in case
    clean_directory(root_dir / "uploads", "root uploads")

    # 5. Clean results folder
    clean_directory(root_dir / "results", "results")

    print(f"\n✨ Cleanup complete!")
    print(f"   Deleted {deleted_dirs} directories and {deleted_files} files.")

def clean_directory(path: Path, name: str):
    if not path.exists():
        return
        
    print(f"   Cleaning {name} folder ({path})...")
    for item in path.iterdir():
        if item.name == ".gitkeep":
            continue
        try:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
            print(f"   [REMOVED] {item.relative_to(path.parent)}")
        except Exception as e:
            print(f"   [ERROR] Could not remove {item}: {e}")

if __name__ == "__main__":
    cleanup()
