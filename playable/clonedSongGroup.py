import random
from clonedSong import ClonedSong

class ClonedSongGroup:
    def __init__(self, id: str, songs: list[ClonedSong]):
        self.id = id
        self.songs = songs

    def getSongToPlay(self):
        return random.choices([x.song for x in self.songs], weights=[x.probability for x in self.songs], k=1)

    def toJsonObject(self):
        return { 'id': self.id, 'songDistributions': [x.toJsonObject() for x in self.songs]}