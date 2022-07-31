from typing import Callable, Union

class MenuOption:
    def __init__(self, symbol: str, description: str, command: Union[Callable, None]):
        self.symbol = symbol.upper()
        self.description = description
        self.command = command