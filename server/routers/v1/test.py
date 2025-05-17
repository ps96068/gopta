from fastapi import APIRouter


router = APIRouter()


@router.get("/")
async def welcome() -> dict:
    return {"message": "404 page not found"}