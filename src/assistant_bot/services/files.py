import shutil, zipfile
from pathlib import Path
from assistant_bot.services.projects import slugify

ALLOWED_EXT = {".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt", ".py", ".js", ".ts", ".md", ".png", ".jpg", ".jpeg", ".zip"}

def safe_filename(name: str) -> str:
    clean = slugify(Path(name).stem) + Path(name).suffix.lower()
    if ".." in clean or clean.startswith("/"): raise ValueError("Unsafe filename")
    return clean

def validate_upload(name: str, size: int, max_mb: int) -> None:
    if size > max_mb * 1024 * 1024: raise ValueError(f"File exceeds {max_mb} MB limit")
    if Path(name).suffix.lower() not in ALLOWED_EXT: raise ValueError("Unsupported file type")

def store_upload(source: Path, dest_dir: Path, original_name: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_filename(original_name)
    shutil.copyfile(source, dest)
    if dest.suffix == ".zip":
        with zipfile.ZipFile(dest) as zf:
            for member in zf.namelist():
                if member.startswith("/") or ".." in Path(member).parts: raise ValueError("Unsafe ZIP path")
    return dest
