import time
from typing import Optional
import pygame
from BallGroup import BallGroup

from Drawing import Drawing
from GameColors import GameColors
from MoveRecord import MoveRecord
from Tube import Tube
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
        self.__window = pygame.display.set_mode((Drawing.ScreenWidth, Drawing.ScreenHeight), pygame.RESIZABLE)
        self.__tubes = TubeSet(self.__window, Drawing.FullTubes, Drawing.EmptyTubes, Drawing.BallsPerTube)

    def main(self) -> None:
        pygame.init()
        pygame.font.init()

        pygame.display.set_caption("Ball Sort")
        pygame.display.set_icon(pygame.image.load("icon.png"))
        pygame.display.update()

        Drawing.resize(Drawing.ScreenWidth, Drawing.ScreenHeight)

        closing = False
        while not closing:
            # event handling, gets all event from the event queue
            unhandledEvents: list[pygame.Event] = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    closing = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                    self.__tubes = TubeSet(self.__window, Drawing.FullTubes, Drawing.EmptyTubes, Drawing.BallsPerTube)
                elif event.type == pygame.VIDEORESIZE:
                    Drawing.resize(event.w, event.h)
                else:
                    unhandledEvents.append(event)

            self.__window.fill(GameColors.WindowBackground)
            self.__tubes.update(unhandledEvents)
            time.sleep(.01)
            pygame.display.flip()

BallSortGame().main()
