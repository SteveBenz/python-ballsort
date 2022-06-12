import time
import pygame

from GameColors import GameColors
from TubeSet import TubeSet
# import pygame_widgets.button

# To install requirements:
#  py -m pip uninstall pygame
#  py -m pip install pygame_widgets

# TODO:
# Refactor
#   Lose the Drawing class
#   Use the "Update" paradigm of widgets
# Double-clicking a tube does a move
# Buttons:
#   Undo
#   Undo-to-checkpoint
#   ReDo
#   New Game
#   Game Size
# Better like-colors highlight
# Save State
# Allow transfers of partial stacks
# Detect Win and Loss

class BallSortGame:
    def __init__(self):
        self.__window = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        self.__tubes = TubeSet(self.__window, pygame.Rect(0,0,800,600), 16, 3, 6)  # type: ignore

    def main(self) -> None:
        pygame.display.set_caption("Ball Sort")
        pygame.display.set_icon(pygame.image.load("icon.png"))
        pygame.display.update()

        closing = False
        while not closing:
            # event handling, gets all event from the event queue
            unhandledEvents: list[pygame.Event] = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    closing = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                    self.__tubes = TubeSet(self.__window, self.__window.get_rect(), 16, 3, 6) # type: ignore
                elif event.type == pygame.VIDEORESIZE:
                    print("fix resize")
                else:
                    unhandledEvents.append(event)

            self.__window.fill(GameColors.WindowBackground)
            self.__tubes.update(unhandledEvents)
            time.sleep(.01)
            pygame.display.flip()

pygame.init()
pygame.font.init()
BallSortGame().main()
