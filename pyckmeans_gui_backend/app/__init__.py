from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from .config import STATIC_DIR

app = FastAPI()

origins = [
    '*',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix='/api')


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / 'index.html')


app.mount("/", StaticFiles(directory=STATIC_DIR))
