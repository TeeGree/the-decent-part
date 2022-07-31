from typing import Callable
import uuid
from mutagen.easyid3 import EasyID3
import os
from musicPlayer import MusicPlayer
from playable.playable import Playable

class Song(Playable):
    def __init__(self, id: str, fullpath: str, clonedSongGroupId: str):
        if not id:
            id = str(uuid.uuid4())
        self.id = id
        self.song = EasyID3(fullpath)
        self.path = fullpath
        self.filename = os.path.basename(fullpath)
        self.additionalPlayLogic = None
        self.player = None
        self.clonedSongGroupId = clonedSongGroupId

    def getPath(self):
        return self.path

    def getArtist(self) -> str:
        if self.song:
            artist = self.song['artist']
            # may need to adjust length logic for when songs are linked
            if artist and len(artist) == 1:
                return artist[0]

        return 'Unknown'

    def getSongName(self) -> str:
        if self.song:
            title = self.song['title']
            if title and len(title) == 1:
                return title[0]

        if self.filename:
            return self.filename

        return 'Unknown'

    def addExtraPlaySongLogic(self, additionalLogic: Callable[..., None]):
        self.additionalPlayLogic = additionalLogic

    def play(self):
        self.player = MusicPlayer()
        self.player.play(self.path)
        if self.additionalPlayLogic:
            self.additionalPlayLogic()

    def isPlaying(self):
        return self.player and self.player.isPlaying()

    def stopPlaying(self):
        if self.player:
            self.player.stop()

    def getTitle(self):
        def buildTitle(songName, artist):
            return f'{songName} by {artist}'
        
        return buildTitle(self.getSongName(), self.getArtist())

    def toJsonObject(self):
        obj = { 'id': self.id, 'path': self.path }
        if self.clonedSongGroupId:
            obj['cloneId'] = self.clonedSongGroupId

        return obj
