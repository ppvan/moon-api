from typing import List, Optional

from pydantic import BaseModel


class SongCreate(BaseModel):
    title: str
    album: str
    artist: str
    thumbnail: str
    data: str


class SongUpdate(BaseModel):
    title: Optional[str]
    album: Optional[str]
    artist: Optional[str]


class SongRead(BaseModel):
    id: int
    title: str
    album: str
    artist: str
    thumbnail: str
    data: str


class UserCreate(BaseModel):
    firstname: str
    lastname: str
    username: str
    password: str


class UserUpdate(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]


class UserRead(BaseModel):
    id: int
    firstname: str
    lastname: str
    username: str
    hashed_password: str
    avatar: str


class PlaylistCreate(BaseModel):
    label: str


class PlaylistSongAdd(BaseModel):
    song_id: int


class PlaylistRead(BaseModel):
    id: int
    label: str
    songs: List[SongRead]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
