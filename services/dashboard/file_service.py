# services/dashboard/file_service.py

from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


class FileService:
    """Service pentru gestionarea fișierelor."""

    @staticmethod
    def validate_image(file: UploadFile) -> None:
        """Validează fișier imagine."""
        # Verifică extensia
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Format nepermis. Formate acceptate: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Verifică dimensiunea
        file.file.seek(0, 2)  # Mergi la sfârșitul fișierului
        file_size = file.file.tell()
        file.file.seek(0)  # Revino la început

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Fișier prea mare. Maxim permis: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Verifică dacă e imagine validă
        try:
            img = Image.open(file.file)
            img.verify()
            file.file.seek(0)
        except:
            raise HTTPException(
                status_code=400,
                detail="Fișier corupt sau format invalid"
            )

    @staticmethod
    async def save_product_image(
            file: UploadFile,
            product_sku: str
    ) -> Tuple[str, str, int]:
        """Salvează imagine produs și returnează (path, filename, size)."""
        FileService.validate_image(file)

        # Generează nume unic
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{product_sku}_{uuid.uuid4()}{file_ext}"

        # Calea completă
        save_path = Path("static/webapp/img/product") / unique_filename

        # Salvează fișierul
        file_content = await file.read()
        with open(save_path, "wb") as f:
            f.write(file_content)

        return str(save_path), unique_filename, len(file_content)

    @staticmethod
    async def save_blog_image(
            file: UploadFile,
            post_slug: str
    ) -> Tuple[str, str, int]:
        """Salvează imagine blog și returnează (path, filename, size)."""
        FileService.validate_image(file)

        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{post_slug}_{uuid.uuid4()}{file_ext}"

        save_path = Path("static/webapp/img/blog") / unique_filename

        file_content = await file.read()
        with open(save_path, "wb") as f:
            f.write(file_content)

        return str(save_path), unique_filename, len(file_content)

    @staticmethod
    async def save_category_image(
            file: UploadFile,
            category_slug: str
    ) -> str:
        """Salvează imagine categorie și returnează path."""
        FileService.validate_image(file)

        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{category_slug}_{uuid.uuid4()}{file_ext}"

        save_path = Path("static/webapp/img/category") / unique_filename

        file_content = await file.read()
        with open(save_path, "wb") as f:
            f.write(file_content)

        return str(save_path)

    @staticmethod
    def delete_image(image_path: str) -> bool:
        """Șterge fizic imaginea din sistem."""
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def delete_product_images(image_paths: List[str]) -> int:
        """Șterge mai multe imagini și returnează numărul de imagini șterse."""
        deleted = 0
        for path in image_paths:
            if FileService.delete_image(path):
                deleted += 1
        return deleted

    @staticmethod
    def get_default_product_image() -> str:
        """Returnează calea către imaginea default pentru produs."""
        return "static/webapp/img/product/prod_default.png"

    @staticmethod
    def get_default_blog_image() -> str:
        """Returnează calea către imaginea default pentru blog."""
        return "static/webapp/img/blog/blog_default.png"

    @staticmethod
    def get_default_category_image() -> str:
        """Returnează calea către imaginea default pentru categorie."""
        return "static/webapp/img/category/cat_default.png"