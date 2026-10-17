import os
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
zip_path = root.parent / "voice_of_store_updated.zip"

exclude_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "env", "node_modules"}
exclude_extensions = {".pyc", ".pyo", ".pyd"}

print(f"Creating zip at: {zip_path}")
count = 0
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude directories in-place
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in exclude_extensions:
                continue
            if fn.endswith(".sqlite3-journal") or fn.endswith(".sqlite3-wal") or fn.endswith(".sqlite3-shm"):
                continue
            full_path = Path(dirpath) / fn
            rel_path = full_path.relative_to(root)
            zf.write(full_path, arcname=str(rel_path))
            count += 1

print(f"Zip created with {count} files. Size: {zip_path.stat().st_size:,} bytes ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
