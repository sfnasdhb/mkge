import os
import shutil
from pathlib import Path
from fastapi import UploadFile
from src.mkge.config import settings

class LocalStorageService:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_id: str, file: UploadFile) -> str:
        file_extension = Path(file.filename or "").suffix
        file_name = f"{file_id}{file_extension}"
        file_path = self.upload_dir / file_name
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return str(file_path)

    def delete_file(self, file_path: str) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
