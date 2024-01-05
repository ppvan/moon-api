# flake8: noqa

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from database import create_tables
from models import Song
from routes import auth_router, file_router, playlist_router, song_router

FILE_PATH = settings.media_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()

    yield


app = FastAPI(title="Moon", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(song_router)
app.include_router(file_router)
app.include_router(auth_router)
app.include_router(playlist_router)
app.mount("/static", StaticFiles(directory=FILE_PATH), name="static")
