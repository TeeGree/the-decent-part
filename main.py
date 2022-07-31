from consoleLogic.consoleLogic import createAddSongMenu, createPlayMenu
from consoleLogic.createEditPlaylist import createPlaylistMenu
from userSettings import UserSettings
from menu import Menu
from menuOption import MenuOption

settingsFileName = 'the_good_part.settings.json'

with UserSettings(f'./{settingsFileName}') as settings:
    def playMenu():
        createPlayMenu(settings)

    def addSongMenu():
        createAddSongMenu(settings)

    def playlistMenu():
        createPlaylistMenu(settings)

    # set up menu with actions now that settings are available
    menu = Menu('What would you like to do?')
    menu.addMenuOption(MenuOption('PLAY', 'View a list of all songs and select one to play.', playMenu))
    menu.addMenuOption(MenuOption('ADD', 'Provide the path of a directory or file to add to the music library.', addSongMenu))
    menu.addMenuOption(MenuOption('LIST', 'Create/edit playlist.', playlistMenu))
    menu.addMenuOption(MenuOption('EXIT', 'Close the application.', None))

    menu.getAndExecuteMenuCommand()