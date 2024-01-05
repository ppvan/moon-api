from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class PlaylistSongLink(SQLModel, table=True):
    song_id: Optional[int] = Field(
        default=None, foreign_key="song.id", primary_key=True
    )
    playlist_id: Optional[int] = Field(
        default=None, foreign_key="playlist.id", primary_key=True
    )


class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    album: str = Field(index=True)
    artist: str = Field(index=True)
    thumbnail: str
    data: str

    playlists: List["Playlist"] = Relationship(
        back_populates="songs", link_model=PlaylistSongLink
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    firstname: str
    lastname: str
    username: str = Field(index=True)
    hashed_password: str = Field(default=None)
    avatar: str = Field(default="https://avatars.githubusercontent.com/ppvan")

    playlists: List["Playlist"] = Relationship(back_populates="user")


class Playlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str

    user_id: int = Field(default=None, foreign_key="user.id")
    user: User = Relationship(back_populates="playlists")

    songs: List[Song] = Relationship(
        back_populates="playlists", link_model=PlaylistSongLink
    )
