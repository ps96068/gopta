# routers/category.py
#
from fastapi import APIRouter, Depends, HTTPException, status, Security
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from ..db.depends import get_db
# from ..crud import category as category_crud
# from ..schemas.category import *
# from ..routers.auth import get_current_user
# from ..models.user import UserRole
#
router = APIRouter()
#
#
#
# @router.post("/categories/", response_model=CategoryResponse, status_code=201)
# async def create_category(
#     category: CategoryCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user: dict = Security(get_current_user, scopes=["admin"])  # Păstrăm autorizarea pentru admini
# ):
#     """
#     Create a new category.
#
#     This endpoint requires admin privileges.
#     """
#
#     if not current_user["is_admin"] or current_user["role"] not in [UserRole.super_admin, UserRole.manager, UserRole.supervisor]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access denied. You do not have administrator privileges."
#         )
#
#     return True
#     # return await category_crud.create_category(db, category)
#
# #
# # @router.put("/categories/{category_id}/", response_model=Category)
# # async def update_category(
# #     category_id: UUID4,
# #     category: CategoryUpdate,
# #     db: AsyncSession = Depends(get_db),
# #     current_user: dict = Security(get_current_user, scopes=["admin"])  # Păstrăm autorizarea pentru admini
# # ):
# #     """
# #     Update an existing category.
# #
# #     This endpoint requires admin privileges.
# #     """
# #
# #     if not current_user["is_admin"] or current_user["role"] not in [UserRole.super_admin, UserRole.manager, UserRole.supervisor]:
# #         raise HTTPException(
# #             status_code=status.HTTP_403_FORBIDDEN,
# #             detail="Access denied. You do not have administrator privileges."
# #         )
# #
# #     return await category_crud.update_category(db, category_id, category)
# #
# #
# # @router.delete("/categories/{category_id}/")
# # async def delete_category(
# #     category_id: UUID,
# #     db: AsyncSession = Depends(get_db),
# #     current_user: dict = Security(get_current_user, scopes=["admin"])  # Păstrăm autorizarea pentru admini
# # ):
# #     """
# #     Delete a category.
# #
# #     This endpoint requires admin privileges.
# #     """
# #
# #     if not current_user["is_admin"] or current_user["role"] not in [UserRole.super_admin, UserRole.manager, UserRole.supervisor]:
# #         raise HTTPException(
# #             status_code=status.HTTP_403_FORBIDDEN,
# #             detail="Access denied. You do not have administrator privileges."
# #         )
# #
# #     return await category_crud.delete_category(db, category_id)
# #
# #
# # # Public endpoints - Accesibile tuturor utilizatorilor autentificați
# #
# # @router.get("/categories/", response_model=list[Category])
# # async def get_categories(
# #     db: AsyncSession = Depends(get_db),
# #     current_user: dict = Depends(get_current_user)  # Acceptăm orice utilizator autentificat
# # ):
# #     """
# #     Retrieve all categories.
# #     """
# #     return await category_crud.get_categories(db)
# #
# #
# # @router.get("/categories/{category_id}/", response_model=Category)
# # async def get_category(
# #     category_id: UUID,
# #     db: AsyncSession = Depends(get_db),
# #     current_user: dict = Depends(get_current_user)  # Acceptăm orice utilizator autentificat
# # ):
# #     """
# #     Retrieve a specific category by ID.
# #     """
# #     return await category_crud.get_category(db, category_id)
#
#
#
#
#
