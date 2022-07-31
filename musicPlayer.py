from pygame import mixer

class MusicPlayer:
    def __init__(self):
        mixer.init()

    def play(self, path: str):
        # 0 indicates playing has started
        mixer.music.load(path)
        mixer.music.play()

    def stop(self):
        mixer.music.stop()

    def isPlaying(self):
        return mixer.music.get_busy()