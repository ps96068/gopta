from __future__ import annotations

import os
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, event, update, select, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column, Session, validates
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.sql import func


from cfg import Base




class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_unknown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    #new
    author_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    last_modified_by: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)

    image_path: Mapped[str | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    create_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    modified_date: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relație cu produsele

    #new
    category_author: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[author_id],
        back_populates="categories_created"
    )
    last_modifier: Mapped["Staff"] = relationship(
        "Staff",
        foreign_keys=[last_modified_by],
        back_populates="categories_modified"
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")
    interactions: Mapped[list["UserInteraction"]] = relationship(
        "UserInteraction",
        primaryjoin="and_(Category.id == foreign(UserInteraction.target_id), UserInteraction.target_type == 'category')",
        back_populates="category",
        overlaps="product,category,interactions"
    )





    @validates('name')
    def validate_name(self, key, value):
        if not value.strip():
            raise ValueError("Numele categoriei nu poate fi gol sau să conțină doar spații.")
        return value


    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', description='{self.description}')>"



# Eveniment pentru atribuirea imaginii implicite la crearea sau actualizarea unei categorii
# @event.listens_for(Category, "before_insert")
# def set_default_image_if_missing(mapper, connection, target):
#     if not target.image_path or not os.path.exists(os.path.join(os.getcwd(), target.image_path)):
#         target.image_path = DEFAULT_IMAGE_PATH
#         print(f"Default image assigned: {DEFAULT_IMAGE_PATH}")


# @event.listens_for(Category, "before_update")
# def handle_image_update(mapper, connection, target):
#     # Obținem istoricul modificărilor pentru câmpul image_path
#     history = get_history(target, 'image_path')
#     old_value = history.deleted[0] if history.deleted else None
#     new_value = target.image_path
#
#     # Verificăm dacă imaginea anterioară există și nu este cea implicită
#     if old_value and os.path.abspath(old_value) != os.path.abspath(DEFAULT_IMAGE_PATH):
#         # Dacă noua valoare este None sau diferită de vechea valoare
#         if not new_value or new_value != old_value:
#             old_file_path = os.path.join(os.getcwd(), old_value)
#             if os.path.exists(old_file_path):
#                 try:
#                     os.remove(old_file_path)
#                     print(f"Old file deleted: {old_file_path}")
#                 except Exception as e:
#                     print(f"Error deleting old file: {old_file_path}, {e}")
#
#     # Verificăm dacă new_value este UploadFile sau string
#     if isinstance(new_value, str):
#         # Dacă e string, verificăm dacă fișierul există
#         if not new_value or not os.path.exists(os.path.join(os.getcwd(), new_value)):
#             target.image_path = DEFAULT_IMAGE_PATH
#             print(f"Default image assigned: {DEFAULT_IMAGE_PATH}")
#     else:
#         # Dacă nu e string (e None sau UploadFile), setăm valoarea implicită
#         if not new_value:
#             target.image_path = DEFAULT_IMAGE_PATH
#             print(f"Default image assigned: {DEFAULT_IMAGE_PATH}")




# Eveniment pentru ștergerea imaginii fizice asociate unei categorii la eliminare
# @event.listens_for(Category, "after_delete")
# def delete_category_image(mapper, connection, target):
#     if target.image_path and os.path.abspath(target.image_path) != os.path.abspath(DEFAULT_IMAGE_PATH):
#         file_path = os.path.join(os.getcwd(), target.image_path)  # Construim calea absolută
#         if os.path.exists(file_path):  # Verificăm dacă fișierul există
#             try:
#                 os.remove(file_path)  # Ștergem fișierul
#                 print(f"File deleted: {file_path}")
#             except Exception as e:
#                 print(f"Error deleting file: {file_path}, {e}")
#         else:
#             print(f"File does not exist: {file_path}")
#     else:
#         print("Default image not deleted.")

# # Gestionarea răspunsului la request (funcție pentru validare imagini)
# def get_all_categories_with_image_validation(session: Session):
#     print("model Category => ")
#     categories = session.query(Category).all()
#     for category in categories:
#         file_path = os.path.join(os.getcwd(), category.image_path)
#         if not os.path.exists(file_path):  # Dacă fișierul nu există
#             category.image_path = DEFAULT_IMAGE_PATH  # Actualizăm cu imaginea implicită
#     return categories