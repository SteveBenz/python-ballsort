"""
This type stub file was generated by pyright.
"""

from pygame_widgets.dropdown import Dropdown

class ComboBox(Dropdown):
    def __init__(self, win, x, y, width, height, choices, textboxKwargs=..., **kwargs) -> None:
        """Initialise a customisable combo box for Pygame. Acts like a searchable dropdown.

        :param win: Surface on which to draw
        :type win: pygame.Surface
        :param x: X-coordinate of top left
        :type x: int
        :param y: Y-coordinate of top left
        :type y: int
        :param width: Width of button
        :type width: int
        :param height: Height of button
        :type height: int
        :param choices: Possible search values
        :type choices: list(str)
        :param textboxKwargs: Kwargs to be passed to the search box
        :type textboxKwargs: dict(str: Any)
        :param maxResults: The maximum number of results to display
        :type maxResults: int
        :param kwargs: Optional parameters
        """
        ...
    
    def createDropdownChoices(self, x, y, width, height, **kwargs): # -> None:
        """Create the widgets for the choices."""
        ...
    
    def listen(self, events):
        """Wait for input.

        :param events: Use pygame.event.get()
        :type events: list of pygame.event.Event
        """
        ...
    
    def draw(self): # -> None:
        """Draw the widget."""
        ...
    
    def contains(self, x, y): # -> bool:
        ...
    
    def updateSearchResults(self): # -> None:
        """Update the suggested results based on selected text.

        Uses a 'contains' research. Could be improved by other
        search algorithms.
        """
        ...
    


if __name__ == '__main__':
    win = ...
    comboBox = ...
    def output(): # -> None:
        ...
    
    button = ...
    run = ...
