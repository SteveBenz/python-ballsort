import os
from random import randint
import time
from typing import Tuple
import pygame
from pygame.rect import Rect
import pygame_widgets
from pygame_widgets.button import Button
from GameColors import GameColors
from TubeSet import TubeSet
import json

# To install requirements:
#  py -m pip uninstall pygame
#  py -m pip install pygame_widgets

# TODO:
# Refactor
#   Import classes?
# Buttons:
#   Game Size
# Better like-colors highlight
# Allow transfers of partial stacks
# Detect Win and Loss

class BallSortGame:
    __ButtonMargins = 3
    __ButtonWidth = 50
    __ButtonRackWidth = __ButtonWidth + 2*__ButtonMargins
    __ButtonHeight = 20

    __buttons: list[Button] = []

    class __SerializedGameState:
        width: int
        height: int
        ballsPerTube: int
        balls: list[list[int]]

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
    def __load() -> __SerializedGameState:
        try:
            with open(BallSortGame.__stateFileName, 'r') as stateFile:
                jsonSettings = json.load(stateFile)
            loadedState = BallSortGame.__SerializedGameState()
            loadedState.balls = jsonSettings['balls']
            loadedState.ballsPerTube = jsonSettings['ballsPerTube']
            loadedState.height = jsonSettings['height']
            loadedState.width = jsonSettings['width']
            return loadedState
        except:
            defaultState = BallSortGame.__SerializedGameState()
            defaultState.width = 800
            defaultState.height = 600
            defaultState.ballsPerTube = 6
            defaultState.balls = BallSortGame.__generateRandomBallSet(16, 3, defaultState.ballsPerTube)
            return defaultState
    
    def __save(self) -> None:
        state = BallSortGame.__SerializedGameState()
        state.balls = self.__tubes.serialize()
        state.ballsPerTube = self.__tubes.numBallsPerTube
        r = self.__window.get_rect()
        state.height = r.height
        state.width = r.width
        
        with open(BallSortGame.__stateFileName, 'w') as stateFile:
            stateFile.write(json.dumps(state.__dict__, indent=True))
        return None

    def __init__(self):
        settings = BallSortGame.__load()
        screenSize = (settings.width, settings.height)
        self.__window = pygame.display.set_mode(screenSize, pygame.RESIZABLE)
        self.__tubes = TubeSet(self.__window, BallSortGame.getTubesPosition(screenSize), settings.ballsPerTube, settings.balls)  # type: ignore
        r = BallSortGame.getUndoButtonPosition(screenSize)
        for t in [("undo", self.__tubes.undo),
                  ("UNDO", self.__tubes.undoToCheckpoint),
                  ("redo", self.__tubes.redo),
                  ("suggest", self.__tubes.suggest),
                  ("new", self.__restart)]:
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
        balls = BallSortGame.__generateRandomBallSet(self.__tubes.numTotalTubes - self.__tubes.numEmptyTubes, self.__tubes.numEmptyTubes, self.__tubes.numBallsPerTube)
        self.__tubes = TubeSet(self.__window, BallSortGame.getTubesPosition(screenSize.size), self.__tubes.numBallsPerTube, balls)  # type: ignore
    

    @staticmethod
    def __generateRandomBallSet(numFilledTubes: int, numEmptyTubes: int, depth: int) -> list[list[int]]:
        td = numFilledTubes*depth
        a = [0]*td
        for i in range(td):
            a[i] = i % numFilledTubes
        for i in range(td):
            swapWith = randint(i,td-1)
            if swapWith != i:
                h = a[i]
                a[i] = a[swapWith]
                a[swapWith] = h
        batches: list[list[int]] = []
        batch: list[int] = []
        batchCount = 0
        for i in a:
            batch.append(i)
            if len(batch) == depth:
                batchCount += 1
                batches.append(batch)
                batch = []
        for i in range(numEmptyTubes):
            batches.append([])
        return batches

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
        self.__save()

pygame.init()
pygame.font.init()
BallSortGame().main()
