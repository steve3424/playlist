import logging
import os
from pathlib import Path
from fastapi import UploadFile

LOGGER = logging.getLogger(f"playlist.{__name__}")
FILE_CHUNK_SIZE = 1024 * 1024
DATA_DIR = None

async def init() -> bool:
    global DATA_DIR
    DATA_DIR = Path(os.environ["DATA_DIR"])
    DATA_DIR.mkdir(exist_ok=True)
    return True

async def save(file: UploadFile, file_path: Path):
    with file_path.open("wb") as f:
        while chunk := await file.read(FILE_CHUNK_SIZE):
            f.write(chunk)
