from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import os
from sqlalchemy import event, select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history

from models.catalog.category import Category


# models/catalog/signals/category_signals.py


# Definirea constantei pentru imaginea implicită
DEFAULT_IMAGE_PATH = os.path.join("static", "shop", "category", "cat_default.png")


# Eveniment pentru atribuirea imaginii implicite la crearea sau actualizarea unei categorii
def set_default_image_if_missing(mapper, connection, target):
    if not target.image_path or not os.path.exists(os.path.join(os.getcwd(), target.image_path)):
        target.image_path = DEFAULT_IMAGE_PATH
        print(f"Default image assigned: {DEFAULT_IMAGE_PATH}")
        logger.info(f"Default image assigned: {DEFAULT_IMAGE_PATH}")

def handle_image_update(mapper, connection, target):
    # Obținem istoricul modificărilor pentru câmpul image_path
    history = get_history(target, 'image_path')
    old_value = history.deleted[0] if history.deleted else None
    new_value = target.image_path

    # Verificăm dacă imaginea anterioară există și nu este cea implicită
    if old_value and os.path.abspath(old_value) != os.path.abspath(DEFAULT_IMAGE_PATH):
        # Dacă noua valoare este None sau diferită de vechea valoare
        if not new_value or new_value != old_value:
            old_file_path = os.path.join(os.getcwd(), old_value)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                    print(f"Old file deleted: {old_file_path}")
                    logger.info(f"Old file deleted: {old_file_path}")
                except Exception as e:
                    print(f"Error deleting old file: {old_file_path}, {e}")
                    logger.error(f"Error deleting old file: {old_file_path}, {e}")

    # Verificăm dacă new_value este UploadFile sau string
    if isinstance(new_value, str):
        # Dacă e string, verificăm dacă fișierul există
        if not new_value or not os.path.exists(os.path.join(os.getcwd(), new_value)):
            target.image_path = DEFAULT_IMAGE_PATH
            print(f"Default image assigned: {DEFAULT_IMAGE_PATH}")
            logger.info(f"Default image assigned: {DEFAULT_IMAGE_PATH}")
    else:
        # Dacă nu e string (e None sau UploadFile), setăm valoarea implicită
        if not new_value:
            target.image_path = DEFAULT_IMAGE_PATH
            print(f"Default image assigned: {DEFAULT_IMAGE_PATH}")
            logger.info(f"Default image assigned: {DEFAULT_IMAGE_PATH}")

# Eveniment pentru ștergerea imaginii fizice asociate unei categorii la eliminare
def delete_category_image(mapper, connection, target):
    if target.image_path and os.path.abspath(target.image_path) != os.path.abspath(DEFAULT_IMAGE_PATH):
        file_path = os.path.join(os.getcwd(), target.image_path)  # Construim calea absolută
        if os.path.exists(file_path):  # Verificăm dacă fișierul există
            try:
                os.remove(file_path)  # Ștergem fișierul
                print(f"File deleted: {file_path}")
                logger.info(f"File deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting file: {file_path}, {e}")
                logger.error(f"Error deleting file: {file_path}, {e}")
        else:
            print(f"File does not exist: {file_path}")
            logger.warning(f"File does not exist: {file_path}")
    else:
        print("Default image not deleted.")
        logger.info("Default image not deleted.")

# Gestionarea răspunsului la request (funcție pentru validare imagini)
def get_all_categories_with_image_validation(session: Session):
    print("model Category => ")
    categories = session.query(Category).all()
    for category in categories:
        file_path = os.path.join(os.getcwd(), category.image_path)
        if not os.path.exists(file_path):  # Dacă fișierul nu există
            category.image_path = DEFAULT_IMAGE_PATH  # Actualizăm cu imaginea implicită
    return categories





event.listen(Category, "before_insert", set_default_image_if_missing)
event.listen(Category, "before_update", handle_image_update)
event.listen(Category, "after_delete", delete_category_image)