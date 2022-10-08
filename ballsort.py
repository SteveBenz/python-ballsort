import os
import time
from typing import Any, Literal, Optional, Tuple
import pygame
from pygame.rect import Rect
from pygame.event import Event
import pygame_widgets
from pygame_widgets.button import Button
from GameColors import GameColors
from TubeSet import TubeSet
import json

# To install requirements:
#  py -m pip uninstall pygame
#  py -m pip install pygame_widgets

# TODO:
# Better like-colors highlight
# Detect Win and Loss

GameSizes = Literal['big', 'small', 'medium']


class BallSortGame:
    __ButtonMargins = 3
    __ButtonWidth = 50
    __ButtonRackWidth = __ButtonWidth + 2*__ButtonMargins
    __ButtonHeight = 20

    __buttons: list[Button] = []
    __lastSize: GameSizes = 'medium'

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
        
    __stateFileName = os.path.join(os.environ['TEMP'], "pyballsort.json")

    @staticmethod
    def __load() -> Optional[dict[str,Any]]:
        try:
            with open(BallSortGame.__stateFileName, 'r') as stateFile:
                return json.load(stateFile)
        except:
            return None
    
    def __save(self) -> None:
        d = self.__tubes.serialize()
        r = self.__window.get_rect()
        d['width'] = r.width
        d['height'] = r.height
        d['size'] = self.__lastSize
        
        with open(BallSortGame.__stateFileName, 'w') as stateFile:
            stateFile.write(json.dumps(d, indent=True))
        return None

    def __init__(self):
        settings = BallSortGame.__load()
        screenSize = (settings['width'], settings['height']) if settings else (800,600)
        self.__window = pygame.display.set_mode(screenSize, pygame.RESIZABLE, display=0)
        self.__tubes = TubeSet(self.__window, BallSortGame.getTubesPosition(screenSize))
        self.__lastSize = settings['size'] if settings else 'medium'
        if settings:
            self.__tubes.loadGame(settings)
        else:
            self.__tubes.newGame(19, 16, 8)
        r = BallSortGame.getUndoButtonPosition(screenSize)
        for t in [("undo", self.__tubes.undo),
                  ("UNDO", self.__tubes.undoToCheckpoint),
                  ("redo", self.__tubes.redo),
                  ("suggest", self.__tubes.suggest),
                  ("new B", lambda: self.__restart('big')),
                  ("new M", lambda: self.__restart('medium')),
                  ("new S", lambda: self.__restart('small'))]:
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

    def __restart(self, size: GameSizes) -> None:
        if size == 'big':
            self.__tubes.newGame(16, 13, 8)
        elif size == 'small':
            self.__tubes.newGame(8, 6, 4)
        else:
            self.__tubes.newGame(12, 10, 5)
        self.__lastSize = size

    def main(self) -> None:
        pygame.display.set_caption("Ball Sort")
        pygame.display.set_icon(pygame.image.load("icon.png"))
        pygame.display.update()
        timeoutInterval = 5 * 60 # After five minutes of inactivity, shut down.

        closing = False
        timeout = time.time() + timeoutInterval
        while not closing:
            unhandledEvents: list[Event] = []
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    timeout = time.time() + timeoutInterval
    
                if event.type == pygame.QUIT:
                    closing = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                    self.__restart(self.__lastSize)
                elif event.type == pygame.VIDEORESIZE:
                    self.__onResize()
                else:
                    unhandledEvents.append(event)

            if time.time() > timeout:
                closing = True

            self.__window.fill(GameColors.WindowBackground)
            self.__tubes.update(unhandledEvents)
            if self.__tubes.isWin:
                self.__restart(self.__lastSize)

            time.sleep(.01)
            pygame_widgets.update(unhandledEvents) # type: ignore   <-- looks like a pylance bug
            pygame.display.update()
        self.__save()

pygame.init()
pygame.font.init()
BallSortGame().main()
