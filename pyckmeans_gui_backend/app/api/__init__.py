from fastapi import APIRouter
from .file_explorer import router as file_explorer_router

router = APIRouter()
router.include_router(file_explorer_router, prefix='/file_explorer')
