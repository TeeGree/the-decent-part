from os import error, listdir, path
from os.path import isfile, join
import json
from typing import Union
from clonedSong import ClonedSong
from playable.clonedSongGroup import ClonedSongGroup
from playable.playlist import Playlist
from playable.song import Song

# disposable class that will automatically read from the provided json settings file and write to it on close
class UserSettings:
    def __init__(self, settingsFullPath):
        self.settingsFullPath = settingsFullPath
        self.songs: list[Song] = []
        self.songsDict: dict[str, Song] = {}
        # Set of paths to prevent adding duplicate paths
        self.pathsSet: set[str] = set()
        self.playlists: dict[str, Playlist] = {}
        self.playlistNames: set[str] = set()
        self.clonedSongGroups: dict[str, ClonedSongGroup] = {}

    def __enter__(self):
        if not path.exists(self.settingsFullPath):
            with open(self.settingsFullPath, 'w'):
                self.settings = {}
        else:
            with open(self.settingsFullPath, 'r') as settingsFile:
                self.settings = json.load(settingsFile)
                songs: list = self.settings.get('songs')
                if songs:
                    for song in songs:
                        cloneId = None
                        if 'cloneId' in song:
                            cloneId = song['cloneId']
                        self.addSongSimple(song['id'], song['path'], cloneId)
                        self.pathsSet.add(song['path'])

                playlists: list = self.settings.get('playlists')
                if playlists:
                    for playlist in playlists:
                        songs: list[Union[Song, list[Song]]] = []
                        for songId in playlist['songs']:
                            if isinstance(songId, list):
                                subSongs: list[Song] = []
                                for s in songId:
                                    subSongs.append(self.songsDict[s])
                                songs.append(subSongs)
                            else:
                                songs.append(self.songsDict[songId])
                        self.addPlaylistSimple(playlist['id'], playlist['name'], songs)

                playlistDependencies: list = self.settings.get('playlistDependencies')
                if playlistDependencies:
                    for dep in playlistDependencies:
                        id = dep['id']
                        playlist = self.playlists[id]
                        for ds in dep['downstream']:
                            playlist.downstreamPlaylists[ds] = self.playlists[ds]
                        for us in dep['upstream']:
                            playlist.upstreamPlaylists[us] = self.playlists[us]

                clonedSongGroups: list = self.settings.get('clonedSongs')
                if clonedSongGroups:
                    for group in clonedSongGroups:
                        clonedSongs: list[ClonedSong] = []
                        for clonedSong in group['songDistributions']:
                            song = self.songsDict[clonedSong['songId']]
                            probability = clonedSong['probability']
                            clonedSongs.append(ClonedSong(song, probability))
                        id: str = group['id']
                        self.clonedSongGroups[id] = ClonedSongGroup(id, clonedSongs)

        return self

    def __exit__(self, type, value, traceback):
        with open(self.settingsFullPath, 'w') as settingsFile:
            self.settings['songs'] = [song.toJsonObject() for song in self.songs]
            playlists = self.getPlaylistsList()
            self.settings['playlists'] = [playlist.toPlaylistJsonObject() for playlist in playlists]
            self.settings['playlistDependencies'] = [playlist.toDependenciesJsonObject() for playlist in playlists]
            self.settings['clonedSongs'] = [group.toJsonObject() for group in self.clonedSongGroups.values()]
            # update the settings file and close it
            json.dump(self.settings, settingsFile, indent=4)

    def addSongSimple(self, id: str, filepath: str, clonedGroupId: str):
        song = Song(id, filepath, clonedGroupId)
        self.songs.append(song)
        self.songsDict[id] = song

    def addPlaylistSimple(self, id: str, name: str, songs: list[Union[Song, list[Song]]]):
        pl = Playlist(id, name, songs)
        self.playlists[id] = pl
        self.playlistNames.add(name)

    def addSongsFromPath(self, dirPath: str) -> list[Song]:
        songs: list[Song] = []

        def addSong(filepath: str):
            song = Song(None, filepath)
            songs.append(song)
            self.pathsSet.add(filepath)

        # only add the paths if they haven't already been added
        if path.exists(dirPath):
            if isfile(dirPath):
                if dirPath.endswith('.mp3') and dirPath not in self.pathsSet:
                    addSong(dirPath)
            else:
                for file in listdir(dirPath):
                    fullPath = join(dirPath, file)
                    if isfile(fullPath) and file.endswith('.mp3') and fullPath not in self.pathsSet:
                        addSong(fullPath)

        self.songs += songs

        return songs

    def renamePlaylist(self, playlist: Playlist, newName: str):
        self.playlistNames.remove(playlist.name)
        self.playlistNames.add(newName)
        self.playlists[playlist.id].name = newName

    def removeSongFromPlaylist(self, playlist: Playlist, songToRemoveIdxInPlaylist: int):
        # handle linked songs
        # remove an empty playlist
        playlist.removeSong(songToRemoveIdxInPlaylist)
        if len(self.playlists[playlist.id].songs) == 0:
            self.playlists.pop(playlist.id)

    def getPlaylistsList(self) -> list[Playlist]:
        playlists = list(self.playlists.values())
        def getName(p: Playlist):
            return p.name

        playlists.sort(key=getName)

        return playlists

    def addPlaylist(self, name: str, songs: list[Song]):
        if self.hasPlaylist(name):
            raise error(f'Playlist with the name {name} already exists!')
        self.addPlaylistSimple(None, name, songs)

    def deletePlaylist(self, id: str):
        if not id in self.playlists:
            raise error(f'Playlist being deleted doesn\'t exist!')

        self.playlists.pop(id)

    def validatePlaylistForDownstreamOrUpstream(self, playlist: Playlist, toAddToStream: Playlist) -> bool:
        if toAddToStream.id in playlist.downstreamPlaylists:
             return False   
            
        if toAddToStream.id in playlist.upstreamPlaylists:
            return False

        return True

    # these functions are handled by settings, since settings has access to all playlists by id
    def addDownstreamToPlaylist(self, playlist: Playlist, downstream: Playlist) -> bool:
        idsToAdd: set[str] = set()

        # Playlist is already in the downstream
        # Playlist is in the upstream and therefore cannot be added to its downstream
        if not self.validatePlaylistForDownstreamOrUpstream(playlist, downstream):
            return False

        idsToAdd.add(downstream.id)
        for d in downstream.downstreamPlaylists:
            if not self.validatePlaylistForDownstreamOrUpstream(playlist, d):
                return False
            idsToAdd.add(d)

        for id in idsToAdd:
            playlist.downstreamPlaylists[id] = self.playlists[id]

        return True

    def addUpstreamToPlaylist(self, playlist: Playlist, upstream: Playlist) -> bool:
        idsToAdd: set[str] = set()
        
        # Playlist is in the downstream and therefore cannot be added to its upstream
        # Playlist is already in the upstream
        if not self.validatePlaylistForDownstreamOrUpstream(playlist, upstream):
            return False

        idsToAdd.add(upstream.id)
        for d in upstream.upstreamPlaylists:
            if not self.validatePlaylistForDownstreamOrUpstream(playlist, d):
                return False
            idsToAdd.add(d)

        for id in idsToAdd:
            playlist.upstreamPlaylists[id]

        return True

    def hasPlaylist(self, playlistName: str) -> bool:
        return playlistName in self.playlistNames
    
    def getSongs(self):
        return self.songs