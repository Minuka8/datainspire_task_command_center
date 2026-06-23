"""
File storage utility. Currently stores files on local disk under
data/uploads/task_<id>/, but the save_file()/get_file_bytes() interface
is intentionally narrow so a future S3/GCS backend can be swapped in
without touching calling code (Phase 4: cloud storage expansion).
"""

import os
import uuid
from pathlib import Path
from app.database.db import UPLOADS_DIR

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".txt", ".csv", ".zip",
}

MAX_FILE_SIZE_MB = 25


def is_allowed_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def save_file(task_id: int, uploaded_file) -> tuple[bool, str, dict | None]:
    """
    Save a Streamlit UploadedFile to disk under a task-scoped folder.
    Returns (success, message, info_dict) where info_dict has
    file_name, stored_path (relative), file_type, file_size_kb.
    """
    filename = uploaded_file.name
    if not is_allowed_file(filename):
        return False, f"File type not allowed: {Path(filename).suffix}", None

    size_kb = len(uploaded_file.getbuffer()) / 1024
    if size_kb / 1024 > MAX_FILE_SIZE_MB:
        return False, f"File exceeds the {MAX_FILE_SIZE_MB}MB limit.", None

    task_dir = UPLOADS_DIR / f"task_{task_id}"
    task_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex[:10]}_{filename}"
    dest_path = task_dir / unique_name

    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    relative_path = str(dest_path.relative_to(UPLOADS_DIR.parent.parent))
    return True, "File saved.", {
        "file_name": filename,
        "stored_path": relative_path,
        "file_type": ext.lstrip("."),
        "file_size_kb": round(size_kb, 1),
    }


def get_absolute_path(stored_path: str) -> Path:
    base_dir = UPLOADS_DIR.parent.parent
    return base_dir / stored_path


def read_file_bytes(stored_path: str) -> bytes | None:
    path = get_absolute_path(stored_path)
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return f.read()
