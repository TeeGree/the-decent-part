from os import error
from random import shuffle
from typing import Callable, Tuple, Union
import uuid
from playable.playable import Playable
from playable.song import Song

class Playlist(Playable):
    def __init__(self, id: str, name: str, songs: list[Union[Song, list[Song]]]):
        if not id:
            id = str(uuid.uuid4())
        self.id = id
        self.name = name
        self.songs = songs
        def addToSongsDict(song: Song):
            if self.songCountDict.get(song.id):
                self.songCountDict[song.id] += 1
            else:
                self.songCountDict[song.id] = 1

        # track the number of occurrences of each song to make it easier to detect if a song already exists in the playlist
        self.songCountDict: dict[str, int] = {}
        for song in songs:
            if not isinstance(song, list):
                addToSongsDict(song)
            else:
                for s in song:
                    addToSongsDict(s)
        self.isPlaying = False

        self.upstreamPlaylists: dict[str, Playlist] = {}
        self.downstreamPlaylists: dict[str, Playlist] = {}
    
    def getFlattenedSongs(self) -> list[Song]:
        songs: list[Song] = []
        for song in self.songs:
            if isinstance(song, list):
                for s in song:
                    songs.append(s)
            else:
                songs.append(song)

        return songs

    # TODO: Add ability to organize downstream songs within the upstream playlist.
    def getFlattenedSongsIncludingDownstream(self) -> list[Song]:
        songs = self.getFlattenedSongs()

        # get songs from all downstream playlists as well
        for id in self.downstreamPlaylists:
            songs += self.downstreamPlaylists[id].songs

        return songs

    def getLinkableSongs(self) -> list[Tuple[Song, int]]:
        songs: list[Tuple[Song, int]] = []
        for i, song in enumerate(self.songs):
            if not isinstance(song, list):
                songs.append((song, i))
        return songs

    def removeSongFromDict(self, id: str):
        if self.songCountDict.get(id):
            self.songCountDict[id] -= 1
            if self.songCountDict[id] == 0:
                self.songCountDict.pop(id)
        else:
            raise error(f'Can\'t remove song with id "{id}" because it isn\'t in the playlist.')

    def removeSong(self, songToRemoveIdxInPlaylist: int):
        songToRemove = None
        songIdx = 0
        i = 0
        while i < len(self.songs) and not songToRemove:
            song = self.songs[i]
            if isinstance(song, list):
                for j, subSong in enumerate(song):
                    if songIdx == songToRemoveIdxInPlaylist:
                        songToRemove = subSong.pop(j)
                        break
                    songIdx += 1
                # replace the linked songs sublist with the only remaining song
                if len(song) == 1:
                    self.songs[i] = song[0]
            else:
                if songIdx == songToRemoveIdxInPlaylist:
                    songToRemove = self.songs.pop(i)
                songIdx += 1
            i += 1
        
        self.removeSongFromDict(songToRemove.id)

    def addSong(self, songToAdd: Song):
        self.songs.append(songToAdd)

    def linkSongs(self, indicesToLink: list[int]):
        indices = indicesToLink.copy()
        # Since linked songs can be in any order, don't try popping potentially out of order.
        linkedSongs: list[Song] = []
        for i in indices:
            # don't need to use self.removeSong() since we can assume linked song indices aren't included
            linkedSongs.append(self.songs[i])

        self.songs.append(linkedSongs)

        # cleanup
        indices.sort(reverse=True)
        for i in indices:
            self.songs.pop(i)

    def playSong(self, song: Song):
        if self.additionalPlayLogicGenerator:
            extraPlayLogic = self.additionalPlayLogicGenerator(song)
            song.addExtraPlaySongLogic(extraPlayLogic)

        song.play()

    def containsSong(self, song: Song) -> bool:
        return song.id in self.songCountDict

    def addExtraPlaySongLogicGenerator(self, additionalLogicGenerator: Callable[[Song], Callable[..., None]]):
        self.additionalPlayLogicGenerator = additionalLogicGenerator

    def play(self):
        songs = self.getFlattenedSongsIncludingDownstream()
        self.isPlaying = True
        i = 0
        while i < len(songs) and self.isPlaying:
            song = songs[i]
            self.playSong(song)

            i += 1

        self.isPlaying = False

    def shuffle(self):
        songs = self.songs.copy()
        # Add songs from all downstream playlists
        for id in self.downstreamPlaylists:
            songs += self.downstreamPlaylists[id].songs.copy()

        shuffle(songs)
        self.isPlaying = True
        i = 0
        while i < len(songs) and self.isPlaying:
            song = songs[i]
            
            if isinstance(song, list):
                # if linked songs, iterate through all linked songs before going to next shuffled song
                j = 0
                while j < len(song) and self.isPlaying:
                    s = song[j]
                    self.playSong(s)
                    j += 1
            else:
                self.playSong(song)

            i += 1

        self.isPlaying = False

    def toPlaylistJsonObject(self):
        songsToReturn: list[Union[str, list[str]]] = []
        for song in self.songs:
            if isinstance(song, list):
                subSongList: list[str] = []
                for s in song:
                    subSongList.append(s.id)
                songsToReturn.append(subSongList)
            else:
                songsToReturn.append(song.id)
        return { 'id': self.id, 'name': self.name, 'songs': songsToReturn }

    def toDependenciesJsonObject(self):
        return {
            'id': self.id,
            'upstream': list(self.upstreamPlaylists),
            'downstream': list(self.downstreamPlaylists)
        }