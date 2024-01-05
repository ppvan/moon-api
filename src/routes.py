import uuid
from datetime import timedelta
from pathlib import Path
from typing import Annotated, List

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, col, select

from config import settings
from database import get_session
from dependencies import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from models import Playlist, Song, User
from schemas import (
    PlaylistCreate,
    PlaylistRead,
    PlaylistSongAdd,
    SongCreate,
    SongRead,
    SongUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)

song_router = APIRouter(prefix="/songs", tags=["Song"])
playlist_router = APIRouter(prefix="/playlists", tags=["Playlist"])
file_router = APIRouter(prefix="/files", tags=["Files"])
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

FILE_PATH = Path(settings.media_dir)


@song_router.get("/search", response_model=List[SongRead])
async def search(query: str, session: Annotated[Session, Depends(get_session)]):
    stmt = select(Song).where(col(Song.title).regexp_match(query, "i"))
    return session.exec(stmt)


@song_router.get("/", response_model=List[SongRead])
async def get_songs(
    offset: int = 0,
    limit: int = 20,
    *,
    session: Annotated[Session, Depends(get_session)],
):
    stmt = select(Song).limit(limit).offset(offset)

    return session.exec(stmt).all()


@song_router.get("/{song_id}", response_model=SongRead)
async def get_a_song(song_id: int, session: Annotated[Session, Depends(get_session)]):
    return session.get(Song, song_id)


@song_router.post("/", response_model=SongRead)
async def create_song(
    song: SongCreate, session: Annotated[Session, Depends(get_session)]
):
    db_song = Song.model_validate(song)
    session.add(db_song)
    session.commit()
    session.refresh(db_song)

    return db_song


@song_router.delete("/{song_id}")
async def delete_song(song_id: int, session: Annotated[Session, Depends(get_session)]):
    db_song = session.get(Song, song_id)

    if not db_song:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Song not found")

    return {"ok": True}


@song_router.patch("/{song_id}", response_model=SongRead)
async def update_song(
    song_id: int, song: SongUpdate, session: Annotated[Session, Depends(get_session)]
):
    db_song = session.get(Song, song_id)

    if not db_song:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Song not found")

    song_attr = song.dict(exclude_unset=True)

    for key, value in song_attr.items():
        setattr(db_song, key, value)

    session.add(db_song)
    session.commit()
    session.refresh(db_song)

    return db_song


@file_router.post("/")
async def upload_file(file: UploadFile, req: Request, res: Response):
    filename = uuid.uuid4().hex

    mapping = {
        "image/png": ".png",
        "audio/mpeg": ".mp3",
        "image/jpeg": ".jpg",
        "application/octet-stream": ".mp3",
    }

    extension = mapping.get(file.content_type)

    if not extension:
        res.status_code = 400
        return {
            "error": f"Unsupported {file.content_type}  mime type. Accept jpg, png and mp3 only"
        }

    file.file.seek(0)

    async with aiofiles.open(FILE_PATH / f"{filename}{extension}", "wb") as f:
        content = await file.read()
        await f.write(content)

    url = f"{req.base_url}static/{filename}{extension}"

    return {"url": url, "content_type": file.content_type}


@playlist_router.post("/", response_model=PlaylistRead)
async def create_playlist(
    playlist: PlaylistCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    db_playlist = Playlist.model_validate(playlist)
    db_playlist.user = current_user

    session.add(db_playlist)
    session.commit()

    session.refresh(db_playlist)

    return db_playlist


@playlist_router.post("/{playlist_id}", response_model=Playlist)
async def add_song_to_playlist(
    playlist_id: int,
    song_add: PlaylistSongAdd,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    playlist: Playlist = session.get(Playlist, playlist_id)
    song: Song = session.get(Song, song_add.song_id)

    if not all([playlist, song]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid playlist_id or song_id",
        )

    playlist.songs.append(song)

    session.add(playlist)

    session.commit()

    session.refresh(playlist)

    return playlist


@auth_router.get("/playlists", response_model=List[PlaylistRead])
async def get_user_playlists(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user.playlists


@playlist_router.get("{playlist_id}", response_model=PlaylistRead)
async def get_playlist(
    playlist_id: int, session: Annotated[Session, Depends(get_session)]
):
    return session.get(Playlist, playlist_id)


@playlist_router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    playlist: Playlist = session.get(Playlist, playlist_id)

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found"
        )

    playlist.songs.clear()

    session.add(playlist)
    session.commit()

    session.delete(playlist)
    session.add(playlist)
    session.commit()

    return {"ok": True}


@auth_router.post("/signup", response_model=UserRead)
async def sign_up(user: UserCreate, session: Annotated[Session, Depends(get_session)]):
    stmt = select(User).where(User.username == user.username)

    existed_user = session.exec(stmt).one_or_none()

    if existed_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exist"
        )

    db_user = User.model_validate(user)
    db_user.hashed_password = get_password_hash(user.password)

    favorite = Playlist(label="_favorite")
    library = Playlist(label="_library")

    db_user.playlists.extend(favorite, library)
    session.add(db_user)
    session.commit()

    session.refresh(db_user)

    return db_user


@auth_router.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Username or password incorect.")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/profile")
async def get_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@auth_router.patch("/profile", response_model=UserRead)
async def update_profile(
    user: UserUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    user_data = user.dict(exclude_unset=True)

    for key, val in user_data.items():
        setattr(current_user, key, val)

    session.add(current_user)

    session.commit()

    session.refresh(current_user)

    return current_user
