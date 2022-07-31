from genericpath import isfile
from os.path import exists
import queue
import threading
import time
from typing import Union
from menu import Menu
from menuOption import MenuOption
from playable.playlist import Playlist
from playable.song import Song
from userSettings import UserSettings


def createMenu(options: list[MenuOption]):
    menu = Menu('Playback commands:')
    for option in options:
        menu.addMenuOption(option)

    return menu

def consolePlaySong(song: Song, options: list[MenuOption], inputQueue: queue.Queue):
    # show the currently playing song until it finishes
    print(f'Now playing: {song.getTitle()}')
    menu = createMenu(options)
    menu.print()
    
    def handleInput(inputQueue):
        while song.isPlaying():
            playbackCommand = input('Enter command: ')
            if playbackCommand:
                playbackCommandUpper = playbackCommand.upper()
                if playbackCommandUpper and playbackCommandUpper in menu.menuOptionsDict:
                    inputQueue.put(playbackCommandUpper)
            time.sleep(0.01)

    inputThread = threading.Thread(target=handleInput, args=(inputQueue,), daemon=True)
    inputThread.start()

    while song.isPlaying():
        if inputQueue.qsize() > 0:
            commandStr = inputQueue.get()
            command = menu.menuOptionsDict[commandStr].command
            if command:
                command()
    inputThread.join()

def playSong(song: Song):
    inputQueue = queue.Queue()

    def stopSong():
        song.stopPlaying()

    options = [MenuOption('stop', 'Stop playing song', stopSong)]
    def additionalLogic():
        consolePlaySong(song, options, inputQueue)
    song.addExtraPlaySongLogic(additionalLogic)
    song.play()
        

def playPlaylist(playlist: Playlist, shouldShuffle: bool):
    inputQueue = queue.Queue()
        
    print(f'Now playing playlist: {playlist.name}')

    def extraPlaySongLogicGenerator(song: Song):
        def skipSong():
            song.stopPlaying()

        def stopPlaylist():
            # it is important that playlist.isPlaying is set first
            # this is because the song stopping will start the next song
            playlist.isPlaying = False
            song.stopPlaying()

        options = [ \
            MenuOption('skip', 'Skip the current song', skipSong), \
            MenuOption('stop', 'Stop playing the playlist', stopPlaylist) \
        ]

        def additionalLogic():
            consolePlaySong(song, options, inputQueue)

        return additionalLogic

    playlist.addExtraPlaySongLogicGenerator(extraPlaySongLogicGenerator)
    if shouldShuffle:
        playlist.shuffle()
    else:
        playlist.play()

def playPlayable(playable: Union[Song, tuple[Playlist, bool]]):
    if isinstance(playable, Song):
        playSong(playable)
    else: # playlist
        playPlaylist(playable[0], playable[1])

def printSongs(files: list[Song], startIdx: int=0):
    if len(files) > 0:
        displayIdx = startIdx
        i = 0
        while i < len(files):
            f = files[i]
            print(f'{displayIdx+1}: {f.getSongName()}')
            i += 1
            displayIdx += 1

        return displayIdx
    else:
        print('There are no songs :(')
        return startIdx

def printPlaylists(playlists: list[Playlist], startIdx: int=0):
    if len(playlists) > 0:
        print('All playlists:')
        displayIdx = startIdx
        i = 0
        while i < len(playlists):
            f = playlists[i]
            print(f'(S){displayIdx+1}: {f.name}')
            i += 1
            displayIdx += 1
        return displayIdx
    else:
        print('There are no playlists. Try creating one in the main menu!')
        return startIdx

def getPlayableChoice(settings: UserSettings) -> Union[None, Song, tuple[Playlist, bool]]:
    mp3Files = settings.getSongs()

    if len(mp3Files) <= 0:
        return None

    # create a playlist of all playable songs
    allSongsPlaylist = Playlist(None, 'All Songs', mp3Files)
    playlists = [allSongsPlaylist] + settings.getPlaylistsList()

    print('All playable mp3 files:')
    i = printSongs(mp3Files)
    print()
    i = printPlaylists(playlists, i)
    print()

    playables: list[Union[Song, Playlist]] = [*mp3Files, *playlists]
    print('Please enter the number of the song or playlist you would like to play.')
    print('For playlists, prefix your selection with \'S\' to shuffle.')
    option = input('Selection: ')

    shouldShuffle = False
    if len(option) > 0 and option[0].lower() == 's':
        option = option[1:]
        shouldShuffle = True

    if option.isnumeric():
        songIdx = int(option)
        # can't shuffle individual songs
        invalid = shouldShuffle and songIdx < len(mp3Files)
        if not invalid and songIdx > 0 and songIdx <= len(playables):
            playable = playables[songIdx-1]
            if isinstance(playable, Playlist):
                return [playable, shouldShuffle]
            return playable
    
    print('Invalid option!')

def createPlayMenu(settings: UserSettings):
    playable = getPlayableChoice(settings)
    if playable:
        playPlayable(playable)

def createAddSongMenu(settings: UserSettings):
    songpath = input('Provide a path to an mp3 or directory you would like to add to the song database: ')
    if not exists(songpath):
        print('Error adding song path: path does not exist!')
    elif isfile(songpath) and not songpath.endswith('.mp3'):
        print('Error adding song file: file must be an mp3!')
    else:
        addedSongs = settings.addSongsFromPath(songpath)
        for song in addedSongs:
            print(f'Found and adding {song.getTitle()}...')
        numSongs = len(addedSongs)
        songsText = 'song'
        if numSongs == 0 or numSongs > 1:
            songsText += 's'
        print(f'{numSongs} new {songsText} added.')
        print()