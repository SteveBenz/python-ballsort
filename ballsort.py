import time
from typing import Tuple
import pygame
from pygame.rect import Rect
import pygame_widgets
from pygame_widgets.button import Button

from GameColors import GameColors
from TubeSet import TubeSet

# To install requirements:
#  py -m pip uninstall pygame
#  py -m pip install pygame_widgets

# TODO:
# Refactor
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
    __ButtonMargins = 3
    __ButtonWidth = 50
    __ButtonRackWidth = __ButtonWidth + 2*__ButtonMargins
    __ButtonHeight = 20

    __buttons: list[Button] = []

    @staticmethod
    def getTubesPosition(screenSize: Tuple[float,float]) -> Rect:
        w,h = screenSize
        return Rect((w - BallSortGame.__ButtonRackWidth)*.05, 0, (w - BallSortGame.__ButtonRackWidth)*.9, h*.95)

    @staticmethod
    def getButtonColumnPosition(screenSize: Tuple[float,float]) -> Rect:
        w,h = screenSize
        return Rect(w - BallSortGame.__ButtonRackWidth, h*.05, BallSortGame.__ButtonRackWidth, h*.95)

    @staticmethod
    def getUndoButtonPosition(screenSize: Tuple[float,float]) -> Rect:
        w,_ = screenSize
        return Rect(w + BallSortGame.__ButtonMargins - BallSortGame.__ButtonRackWidth, BallSortGame.__ButtonMargins, BallSortGame.__ButtonWidth, BallSortGame.__ButtonHeight)

    def __init__(self):
        defaultScreenSize = (800,600)
        self.__window = pygame.display.set_mode(defaultScreenSize, pygame.RESIZABLE)
        self.__tubes = TubeSet(self.__window, BallSortGame.getTubesPosition(defaultScreenSize), 16, 3, 6)  # type: ignore
        r = BallSortGame.getUndoButtonPosition(defaultScreenSize)
        for t in [("undo", self.__tubes.undo), ("UNDO", self.__tubes.undoToCheckpoint), ("redo", self.__tubes.redo), ("new", self.__restart)]:
            text, action = t
            self.__buttons.append(
                Button(self.__window, r.left, r.top, r.width, r.height, **{"text": text, "onClick": action})
            )
            r = r.move(0, r.height + BallSortGame.__ButtonMargins)

    def __setButtonPos(self, b: Button, r: Rect) -> None:
        b.setX(r.left) # type: ignore
        b.setY(r.top) # type: ignore
        b.setWidth(r.width) # type: ignore
        b.setHeight(r.height) # type: ignore

    def __onResize(self):
        screenSize = self.__window.get_rect()
        self.__tubes.reposition(BallSortGame.getTubesPosition(screenSize.size)) # type: ignore  Rect rect.Rect
        r = BallSortGame.getUndoButtonPosition(screenSize.size)
        for b in self.__buttons:
            self.__setButtonPos(b, r)
            r = r.move(0, r.height + BallSortGame.__ButtonMargins)

    def __restart(self):
        screenSize = self.__window.get_rect()
        self.__tubes = TubeSet(self.__window, BallSortGame.getTubesPosition(screenSize.size), 16, 3, 6) # type: ignore

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
                    self.__restart()
                elif event.type == pygame.VIDEORESIZE:
                    self.__onResize()
                else:
                    unhandledEvents.append(event)

            self.__window.fill(GameColors.WindowBackground)
            self.__tubes.update(unhandledEvents)
            time.sleep(.01)
            pygame_widgets.update(unhandledEvents) # type: ignore
            pygame.display.update()

pygame.init()
pygame.font.init()
BallSortGame().main()
