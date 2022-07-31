from playable.song import Song

class ClonedSong:
    def __init__(self, song: Song, probability: int):
        self.song = song
        self.probability = probability

    def toJsonObject(self):
        return { 'songId': self.song.id, 'probability': self.probability }