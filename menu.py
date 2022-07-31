from typing import Callable
from menuOption import MenuOption


class Menu:
    def __init__(self, initialPrompt: str):
        self.initialPrompt = initialPrompt
        self.menuOptionsDict = {}
        self.menuOptionsList: list[MenuOption] = []

    def addMenuOption(self, option: MenuOption):
        self.menuOptionsDict[option.symbol] = option
        self.menuOptionsList.append(option)

    def print(self):
        print(self.initialPrompt)
        print()
        for option in self.menuOptionsList:
            print(f'{option.symbol} - {option.description}')

        print()

    def getAndExecuteMenuCommand(self, prompt: str = 'Enter menu option: ', stopCondition: Callable = None):
        def getCommand():
            if stopCondition and stopCondition():
                return None
                
            self.print()
            option = input(prompt).upper()
            while option not in self.menuOptionsDict and (not stopCondition or not stopCondition()):
                print('Invalid option!')
                option = input(prompt).upper()
            if option in self.menuOptionsDict:
                return self.menuOptionsDict[option].command

            return None

        command = getCommand()
        while command and (not stopCondition or not stopCondition()):
            command()
            command = getCommand()