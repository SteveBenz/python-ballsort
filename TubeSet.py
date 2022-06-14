import math
import time
from typing import Callable, Iterable, Optional, Tuple

import pygame
from BallGroup import BallGroup
from MoveRecord import MoveRecord
from Tube import Tube


class TubeSet:

    __keyboardHintCharacters = (
        '1', '2', '3', '4', '5',
        'q', 'w', 'e', 'r', 't',
        'a', 's', 'd', 'f', 'g',
        'z', 'x', 'c', 'v', 'b'
    )

    __tubeKeys = (
        pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
        pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t,
        pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g,
        pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b
    )

    def __init__(self, window: pygame.Surface, rect: pygame.Rect, depth: int, balls:Iterable[Iterable[int]]):
        self.__window = window
        self.__depth = depth
        self.__rect = rect

        self.__tubes: list[Tube] = []
        i = 0
        ballsList = list(balls)
        for tubeRect in TubeSet.__getTubeLayout(rect, len(ballsList), depth):
            self.__tubes.append(Tube(window, tubeRect, TubeSet.__keyboardHintCharacters[i], depth))
            i += 1

        i = 0
        for batch in ballsList:
            tube = self.__tubes[i]
            i += 1
            for color in batch:
                tube.push(BallGroup(color=color, count=1))

        self.__undoStack: list[MoveRecord] = []
        self.__redoStack: list[MoveRecord] = []
        self.__pendingMove: Optional[Tube] = None
    
    def serialize(self) -> list[list[int]]:
        batches: list[list[int]] = []
        for t in self.__tubes:
            batches.append(t.serialize())
        return batches

    def reposition(self, rect: pygame.Rect) -> None:
        i = 0
        for l in TubeSet.__getTubeLayout(rect, len(self.__tubes), self.__depth):
            self.__tubes[i].rect = l
            i += 1
        self.__rect = rect

    @staticmethod
    def __getTubeLayout(rect: pygame.Rect, numTubes: int, numBalls: int) -> Iterable[pygame.Rect]:
        # Hard-coding to a two-row.  Better if we adjusted it based on the layout
        rows = 2
        columns = (numTubes+1)//2
        (width,height) = Tube.getMaxUsableSize((rect.width / columns, rect.height / rows), numBalls)

        # It'd be better if the extra space was distributed between rows and columns
        for i in range(numTubes):
            row = i // columns
            column = i % columns
            yield pygame.Rect(width*column + rect.left, height*row + rect.top, width, height)

    def isTubeKeyboardShortcut(self, keyboardId: int) -> bool:
        return keyboardId in TubeSet.__tubeKeys

    def getTubeForKeyStroke(self, keyboardId: int) -> Tube:
        return self.__tubes[TubeSet.__tubeKeys.index(keyboardId)]

    def draw(self) -> None:
        for tube in self.__tubes:
            tube.draw(
                canAddHighlight=self.__pendingMove is not None and self.__pendingMove is not tube and tube.canAddBallGroup(self.__pendingMove.peek()),
                isSourceHighlight=self.__pendingMove is tube,
                highlightedColor=self.__pendingMove.peek().color if self.__pendingMove else None)
    
    def tryGetAutoMove(self, source: Tube) -> Optional[Tube]:
        emptyValidMove = None
        for t in self.__tubes:
            if source is t: continue
            if t.get_isEmpty():
                if emptyValidMove is None:
                    emptyValidMove = t
            elif t.canAddBallGroup(source.peek()):
                return t
        return emptyValidMove            
    
    def tryFindMove(self, existingMove: Optional[Tube]) -> Optional[Tube]:
        hitExistingMove = existingMove is None
        firstValidMove = None
        for source in self.__tubes:
            if source.get_isEmpty():
                continue
            sourcePeek = source.peek()
            for target in self.__tubes:
                if target is not source and target.canAddBallGroup(sourcePeek):
                    if firstValidMove is None:
                        firstValidMove = source
                    if source is existingMove:
                        hitExistingMove = True
                    elif hitExistingMove:
                        return source
        return firstValidMove

    def tryFindTubeByPosition(self, position: Tuple[int,int]) -> Optional[Tube]:
        for t in self.__tubes:
            if t.rect.collidepoint(position):
                return t
        return None
    
    @property
    def numEmptyTubes(self) -> int:
        return sum(1 for t in self.__tubes if t.get_isEmpty())

    @property
    def numTotalTubes(self) -> int:
        return len(self.__tubes)

    @property
    def numBallsPerTube(self) -> int:
        return self.__depth

    @staticmethod
    def interpolatePosition(start: Tuple[float,float], end: Tuple[float,float], progress: float) -> Tuple[float,float]:
        return start[0] + (end[0]-start[0])*progress, start[1] + (end[1]-start[1])*progress

    @staticmethod
    def interpolate(waypoints: list[Tuple[float, float]]) -> Callable[[float], Tuple[float,float]]:
        totalLength = -1.0
        lengths: list[float] = list()
        lastWaypoint = (0.0,0.0)
        for pair in waypoints:
            if totalLength < 0:
                lastWaypoint = pair
                totalLength = 0
            else:
                dx = pair[0] - lastWaypoint[0]
                dy = pair[1] - lastWaypoint[1]
                length = math.sqrt(dx*dx+dy*dy)
                totalLength += length
                lastWaypoint = pair
                lengths.append(length)
        def interpolation(progress: float) -> Tuple[float,float]:
            index = 0
            totalLengthSoFar = 0.0
            while totalLengthSoFar < progress * totalLength:
                totalLengthSoFar += lengths[index]
                index += 1
            # index is the next waypoint - we're between waypoints[index-1] and waypoints[index]
            priorWaypointDistance = 0.0
            for i in range(index-1): priorWaypointDistance += lengths[i]
            progressBetweenPoints = (totalLength*progress - priorWaypointDistance)/lengths[index-1]
            x = waypoints[index-1][0] + (waypoints[index][0] - waypoints[index-1][0])*progressBetweenPoints
            y = waypoints[index-1][1] + (waypoints[index][1] - waypoints[index-1][1])*progressBetweenPoints
            return x,y
        return interpolation
    
    def makeSelectionAnimator(self, selection: Tube, isIncoming: bool) -> Callable[[float], pygame.Rect]:
        selectionGroup = selection.peek()
        topBallRectHigh = selection.getBallPosition(selection.emptySlots-.5)
        bottomBallRect = selection.getBallPosition(selection.emptySlots+selectionGroup.count-1)
        animationArea = topBallRectHigh.union(bottomBallRect)
        background = pygame.Surface(animationArea.size)

        _ = selection.pop()
        selection.draw(
            canAddHighlight=False,
            isSourceHighlight=False,
            highlightedColor=selectionGroup.color)
        background.blit(self.__window, (0,0), animationArea)
        selection.push(selectionGroup)
        ballImage = selection.getBallImage(selectionGroup.color, isHighlighted=True)
        def animation(position: float) -> pygame.Rect:
            self.__window.blit(background, animationArea)
            for ballTubePosition in range(selection.emptySlots, selection.emptySlots+selectionGroup.count):
                target = selection.getBallPosition(ballTubePosition - .5*(position if isIncoming else 1-position))
                self.__window.blit(ballImage, target)
            return animationArea  # type: ignore
        return animation
    
    def animateSelection(self, newSelection: Optional[Tube], oldSelection: Optional[Tube]) -> None:
        newAnimation = self.makeSelectionAnimator(newSelection, True) if newSelection else None
        oldAnimation = self.makeSelectionAnimator(oldSelection, False) if oldSelection else None
        startTime = time.time()
        animationDuration = .1 # seconds
        progress = 0.0
        while progress < 1:
            progress = (time.time() - startTime) / animationDuration
            if progress >= 1:
                progress = 1
            updateAreas: list[pygame.Rect] = []
            if newAnimation:
                updateAreas.append(newAnimation(progress))
            if oldAnimation:
                updateAreas.append(oldAnimation(progress))
            pygame.display.update(updateAreas)  # type: ignore   Looks like a pylance bug

    def animateMove(self, source: Tube, target: Tube, moving: BallGroup, sourceIsSelected: bool) -> None:
        self.__pendingMove = None
        self.draw()
        background = pygame.surface.Surface(self.__rect.size)
        background.blit(self.__window, (0,0), self.__rect)
        interpolatorFunctions: list[Callable[[float], Tuple[float,float]]] = []
        ballImage = source.getBallImage(moving.color, isHighlighted=False)

        topOfSourceTube: Tuple[float,float] = source.getBallPosition(-1).topleft
        topOfTargetTube: Tuple[float,float] = target.getBallPosition(-1).topleft
        for i in range(moving.count):
            start: Tuple[float,float] = source.getBallPosition(source.emptySlots - moving.count + i - (.5 if sourceIsSelected else 0)).topleft
            end: Tuple[float,float] = target.getBallPosition(target.emptySlots - 1 - i).topleft
            interpolatorFunctions.append( \
                TubeSet.interpolate( [start,topOfSourceTube,topOfTargetTube,end] ))

        startTime = time.time()
        animationDuration = .25 # seconds
        progress = 0
        while progress < 1:
            progress = (time.time() - startTime) / animationDuration
            if progress >= 1:
                progress = 1
            self.__window.blit(background, self.__rect.topleft)
            for f in interpolatorFunctions:
                topLeft = f(progress)
                self.__window.blit(ballImage, topLeft)
            pygame.display.update(self.__rect)

    def setPendingMove(self, selectedTube: Optional[Tube]) -> None:
        if selectedTube is not self.__pendingMove:
            self.animateSelection(selectedTube, self.__pendingMove)
            self.__pendingMove = selectedTube

    def doMove(self, selectedTube: Tube):
        def actuallyDoMove(source: Tube, target: Tube) -> None:
            self.__undoStack.append(MoveRecord(source, target))
            self.__redoStack.clear()
            moving = source.pop()
            self.animateMove(source, target, moving, True)
            target.push(moving)
            self.__pendingMove = None

        if self.__pendingMove and self.__pendingMove is selectedTube:
            target = self.tryGetAutoMove(self.__pendingMove)
            if target:
                actuallyDoMove(self.__pendingMove, target)
            else:
                self.setPendingMove(None)
        elif self.__pendingMove is None and selectedTube is not None and not selectedTube.get_isEmpty():
            self.setPendingMove(selectedTube)
        elif self.__pendingMove is not None and selectedTube is not None and selectedTube.canAddBallGroup(self.__pendingMove.peek()):
            actuallyDoMove(self.__pendingMove, selectedTube)
        elif not selectedTube.get_isEmpty():
            self.setPendingMove(selectedTube)

    def undo(self):
        self.setPendingMove(None)
        if not self.__undoStack:
            return
        moveToUndo = self.__undoStack.pop()
        moving = BallGroup(color = moveToUndo.target.peek().color, count = moveToUndo.count)
        moveToUndo.target.removeBalls(moveToUndo.count)
        self.animateMove(moveToUndo.target, moveToUndo.source, moving, False)
        moveToUndo.source.push(moving)
        self.__redoStack.append(moveToUndo)

    def redo(self):
        self.setPendingMove(None)
        if not self.__redoStack:
            return
        moveToRedo = self.__redoStack.pop()
        moving = BallGroup(color = moveToRedo.source.peek().color, count = moveToRedo.count)
        moveToRedo.source.removeBalls(moveToRedo.count)
        self.animateMove(moveToRedo.source, moveToRedo.target, moving, False)
        moveToRedo.target.push(moving)
        self.__undoStack.append(moveToRedo)

    def undoToCheckpoint(self):
        self.setPendingMove(None)
        oldEmptyCount = self.numEmptyTubes
        while any(self.__undoStack) and self.numEmptyTubes <= oldEmptyCount:
            self.undo()

    def suggest(self):
        self.setPendingMove(self.tryFindMove(self.__pendingMove))


    def update(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.setPendingMove(None)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.suggest()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL and event.mod & pygame.KMOD_SHIFT:
                self.undoToCheckpoint()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL:
                self.undo()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_y and event.mod & pygame.KMOD_CTRL:
                self.redo()
            elif event.type == pygame.KEYDOWN and (self.isTubeKeyboardShortcut(event.key) or event.key == pygame.K_SPACE):
                if event.key == pygame.K_SPACE:
                    selectedTube = None if self.__pendingMove is None else self.tryGetAutoMove(self.__pendingMove)
                else:
                    selectedTube = self.getTubeForKeyStroke(event.key)

                if selectedTube is not None:
                    self.doMove(selectedTube)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                (x,y) = event.pos
                selectedTube: Optional[Tube] = self.tryFindTubeByPosition((x,y))
                if selectedTube is not None:
                    self.doMove(selectedTube)
        self.draw()
