from typing import Callable
from consoleLogic.consoleLogic import printSongs
from menu import Menu
from menuOption import MenuOption
from playable.playlist import Playlist
from playable.song import Song
from userSettings import UserSettings

def promptForSongs(settings: UserSettings, prompt: str, validateSong: Callable[[Song], bool], whatToDoWithEachSong: Callable[[Song], None]):
    mp3Files = settings.getSongs()
    # playlists with 0 songs are valid
    if len(mp3Files) <= 0:
        print('There are no playable songs. Please add songs via the main menu first.')
        return None

    print()
    print(prompt)

    def getOptionLoop() -> str:
        print()
        print('All playable songs:')
        printSongs(mp3Files)
        print()

        return input('Please enter the number of the song or playlist you would like to add or STOP to stop adding songs: ')

    option = getOptionLoop()

    while option.upper() != 'STOP':
        if option.isnumeric():
            songIdx = int(option)
            if songIdx > 0 and songIdx <= len(mp3Files):
                song = mp3Files[songIdx-1]
                if not validateSong(song):
                    confirm = input('Would you still like to add the song? (yes/no):')
                    while confirm.lower() != 'yes' and confirm.lower() != 'no':
                        confirm = input('Would you still like to add the song? (yes/no):')
                    if confirm.lower() == 'yes':
                        whatToDoWithEachSong(song)
                else:
                    whatToDoWithEachSong(song)
            else:
                print('Invalid option!')
        else:
            print('Invalid option!')

        option = getOptionLoop()

def createNewPlaylistMenu(settings: UserSettings):
    def validatePlaylistName(playlistName: str) -> bool:
        if len(playlistName) == 0:
            return False
        if settings.hasPlaylist(playlistName):
            print('Playlist already exists!')
            return False
        return True

    name = input('Enter name for new playlist: ')

    while not validatePlaylistName(name):
        name = input('Enter name for new playlist: ')

    songs: list[Song] = []
    songIds: set[str] = set()
    def addSong(song: Song):
        songs.append(song)
        songIds.add(song.id)

    # check to see if the song has already been added
    def validateSong(song: Song) -> bool:
        print('This song has already been added to the new playlist!')
        return not song.id in songIds

    promptForSongs(settings, 'Create a playlist from the playable songs:', validateSong, addSong)

    settings.addPlaylist(name, songs)

def renamePlaylist(settings: UserSettings, playlist: Playlist):
    oldName = playlist.name
    newName = input(f'Enter the new name for the "{oldName}" playlist: ')
    settings.renamePlaylist(playlist, newName)

    print(f'Playlist "{oldName}" has been renamed to "{newName}"!')

def addSongsToPlaylist(settings: UserSettings, playlist: Playlist):
    songsToAdd: list[Song] = []
    songIdsToAdd: set[str] = set()

    def addSong(song: Song):
        songsToAdd.append(song)
        songIdsToAdd.add(song.id)

    def validateSong(song: Song):
        if playlist.containsSong(song):
            print('This song already exists in the playlist!')
            return False

        if song.id in songIdsToAdd:
            print('This song has already been selected to be added to the playlist!')
            return False

        return True
    
    promptForSongs(settings, f'Add songs to playlist "{playlist.name}":', validateSong, addSong)

    for song in songsToAdd:
        playlist.addSong(song)

def promptForAndActOnSelectedPlaylist(settings: UserSettings, playlist: Playlist, prompt: str, whatToDoWithPlaylist: Callable[[Playlist], None]):
    print(prompt)
    print()
    print('Playlists:')
    playlists = settings.getPlaylistsList()
    possiblePlaylists: list[Playlist] = []
    i = 1
    for p in playlists:
        if p.id != playlist.id:
            possiblePlaylists.append(p)
            print(f'{i} - {p.name}')
            i += 1

    print()
    selection = input('Enter the number of playlist or CANCEL: ')
    while selection.upper() != 'CANCEL':
        if selection.isnumeric():
            playlistNum = int(selection)
            if playlistNum <= len(possiblePlaylists) and playlistNum > 0:
                selectedPlaylist = possiblePlaylists[playlistNum-1]
                whatToDoWithPlaylist(selectedPlaylist)
                return
            else:
                print('Invalid selection!')
        else:
            print('Invalid selection!')

        selection = input('Enter the number of playlist or CANCEL: ')

def addSongsFromPlaylistToPlaylist(settings: UserSettings, playlist: Playlist):
    prompt = f'Select another playlist. All of the songs from that playlist will be added to {playlist.name}'

    def addSongs(selectedPlaylist: Playlist):
        for s in selectedPlaylist.getFlattenedSongsIncludingDownstream():
            playlist.addSong(s)
            print(f'Added {s.getTitle()} to {playlist.name}!')

    promptForAndActOnSelectedPlaylist(settings, playlist, prompt, addSongs)

def addDownstreamPlaylist(settings: UserSettings, playlist: Playlist):
    prompt = f'Select another playlist. That playlist will be added as a downstream playlist to {playlist.name}'

    def addDownstream(selectedPlaylist: Playlist):
        success = settings.addDownstreamToPlaylist(playlist, selectedPlaylist)
        if success:
            print(f'Added {selectedPlaylist.name} as a downstream playlist to {playlist.name}!')
        else:
            print(f'Failed to add {selectedPlaylist.name} as a downstream playlist to {playlist.name}!')

    promptForAndActOnSelectedPlaylist(settings, playlist, prompt, addDownstream)

def removeSongsFromPlaylist(settings: UserSettings, playlist: Playlist):
    option = ''
    while len(playlist.songs) > 0 and option.upper() != 'STOP':
        flattenedSongs = playlist.getFlattenedSongs()
        printSongs(flattenedSongs)
        option = input('Please enter the number of the song you would like to remove from the playlist or STOP to stop removing songs: ')

        if option.isnumeric():
            idx = int(option)
            if idx <= len(flattenedSongs) and idx > 0:
                songToRemove = flattenedSongs[idx-1]
                settings.removeSongFromPlaylist(playlist, idx-1)
                print(f'{songToRemove.getSongName()} has been removed from {playlist.name}!')
                if len(playlist.songs) == 0:
                    print(f'All songs have been removed from "{playlist.name}"! "{playlist.name}" has been deleted!')
            else:
                print('Invalid selection!')
        elif option.upper() != 'STOP':
            print('Invalid selection!')

def linkSongsMenu(playlist: Playlist):
    # currently don't allow even selecting songs that are already linked
    songsWithIdx = playlist.getLinkableSongs()
    if len(songsWithIdx) <= 1:
        print('There are not enough songs to link. Please add songs via the main menu first.')
        return None

    print()
    print('Choose songs to link:')

    selectedIndices: list[int] = []

    def getOptionLoop() -> str:
        print()
        print('Songs in playlist:')
        songs = [x[0] for x in songsWithIdx]
        printSongs(songs)
        print()
        if len(selectedIndices) > 0:
            linkedSongs: list[str] = [playlist.songs[x].getSongName() for x in selectedIndices]
            linkedSongsText = ', '.join(linkedSongs)
            print(f'Songs already in link: [{linkedSongsText}]')

        return input('Please enter the number of the song you would like to link or STOP to stop linking songs: ')

    option = getOptionLoop()

    while option.upper() != 'STOP':
        if option.isnumeric():
            songIdx = int(option)
            if songIdx > 0 and songIdx <= len(songsWithIdx):
                selection = songsWithIdx.pop(songIdx-1)
                selectedIndices.append(selection[1])
            else:
                print('Invalid option!')
        else:
            print('Invalid option!')

        option = getOptionLoop()

    if len(selectedIndices) > 1:
        playlist.linkSongs(selectedIndices)

def chooseEditPlaylistActionMenu(settings: UserSettings, playlist: Playlist):
    def getInitialPrompt():
        return f'What would you like to do with "{playlist.name}"?'
    
    menu = Menu(getInitialPrompt())

    def renamePlaylistWrapper():
        renamePlaylist(settings, playlist)
        # reset initial prompt to reflect new playlist name
        menu.initialPrompt = getInitialPrompt()

    def addSongsToPlaylistWrapper():
        addSongsToPlaylist(settings, playlist)

    def addSongsFromPlaylistToPlaylistWrapper():
        addSongsFromPlaylistToPlaylist(settings, playlist)

    def addDownstreamPlaylistWrapper():
        addDownstreamPlaylist(settings, playlist)

    def removeSongsFromPlaylistWrapper():
        removeSongsFromPlaylist(settings, playlist)

    def linkSongsMenuWrapper():
        linkSongsMenu(playlist)

    def shouldStopEditing():
        return len(playlist.songs) == 0
    
    menu.addMenuOption(MenuOption('RENAME', 'Rename playlist.', renamePlaylistWrapper))
    menu.addMenuOption(MenuOption('ADD', 'Add songs', addSongsToPlaylistWrapper))
    menu.addMenuOption(MenuOption('ADDPLAY', 'Add songs from playlist', addSongsFromPlaylistToPlaylistWrapper))
    menu.addMenuOption(MenuOption('ADDDOWN', 'Add downstream playlist', addDownstreamPlaylistWrapper))
    menu.addMenuOption(MenuOption('REMOVE', 'Remove songs', removeSongsFromPlaylistWrapper))
    menu.addMenuOption(MenuOption('LINK', 'Link songs so that they always play back to back during shuffle.', linkSongsMenuWrapper))
    menu.addMenuOption(MenuOption('BACK', 'Back to main menu.', None))
    menu.getAndExecuteMenuCommand(stopCondition=shouldStopEditing)

def editPlaylistMenu(settings: UserSettings):
    playlists = settings.getPlaylistsList()
    if not playlists or len(playlists) == 0:
        print('There are no playlists.')
        return

    print('Playlists:')
    for i, playlist in enumerate(playlists):
        print(f'{i+1} - {playlist.name}')

    print()
    idx = input('Please enter the number of the playlist you would like to edit: ')
    if idx.isnumeric():
        idx = int(idx)
        if idx <= len(playlists) and idx > 0:
            playlist = playlists[idx-1]
            chooseEditPlaylistActionMenu(settings, playlist)

def deletePlaylistMenu(settings: UserSettings):
    playlists = settings.getPlaylistsList()
    if not playlists or len(playlists) == 0:
        print('There are no playlists.')
        return

    print('Playlists:')
    for i, playlist in enumerate(playlists):
        print(f'{i+1} - {playlist.name}')

    print()
    idx = input('Please enter the number of the playlist you would like to delete: ')
    if idx.isnumeric():
        idx = int(idx)
        if idx <= len(playlists) and idx > 0:
            playlist = playlists[idx-1]
            settings.deletePlaylist(playlist.id)
            print(f'Playlist "{playlist.name}" has been deleted!')

def createPlaylistMenu(settings: UserSettings):
    def createNewPlaylistMenuWrapper():
        createNewPlaylistMenu(settings)

    def editPlaylistMenuWrapper():
        editPlaylistMenu(settings)

    def deletePlaylistMenuWrapper():
        deletePlaylistMenu(settings)

    menu = Menu('What would you like to do?')
    menu.addMenuOption(MenuOption('CREATE', 'Create a new playlist.', createNewPlaylistMenuWrapper))
    menu.addMenuOption(MenuOption('EDIT', 'Edit playlist.', editPlaylistMenuWrapper))
    menu.addMenuOption(MenuOption('DELETE', 'Delete playlist.', deletePlaylistMenuWrapper))
    menu.addMenuOption(MenuOption('BACK', 'Back to main menu.', None))

    menu.getAndExecuteMenuCommand()