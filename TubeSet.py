
from array import array
import math
import random
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

    def __init__(self, window: pygame.Surface, rect: pygame.Rect, numTubes: int, numFreeTubes: int, depth: int):
        self.__window = window
        a = array('i', [0]*numTubes*depth)
        td = numTubes*depth
        for i in range(td):
            a[i] = i % numTubes
        for i in range(td):
            swapWith = random.randint(i,td-1)
            if swapWith != i:
                h = a[i]
                a[i] = a[swapWith]
                a[swapWith] = h

        # Hard code to a two-row setup with 10% space above each.
        self.tubes: list[Tube] = []
        i = 0
        for tubeRect in TubeSet.__getTubeLayout(rect, numTubes + numFreeTubes, depth):
            self.tubes.append(Tube(window, tubeRect, TubeSet.__keyboardHintCharacters[i], depth))
            i += 1

        for i in range(numTubes):
            for j in range(depth):
                self.tubes[i].push(BallGroup(color=a[i*depth+j], count=1))

        self.undoStack: list[MoveRecord] = []
        self.redoStack: list[MoveRecord] = []
        self.pendingMove: Optional[Tube] = None

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
            yield pygame.Rect(width*column, height*row, width, height)

    # Tests to see if the top color block can be moved and, if so, to which
    # tubes could it be added.
    def canMove(self, slot: Tube) -> list[Tube]:
        if slot.get_isEmpty(): return list()
        return list(filter(lambda t: t != slot and slot.canAddBallGroup(slot.peek()), self.tubes))

    def isTubeKeyboardShortcut(self, keyboardId: int) -> bool:
        return keyboardId in TubeSet.__tubeKeys

    def getTubeForKeyStroke(self, keyboardId: int) -> Tube:
        return self.tubes[TubeSet.__tubeKeys.index(keyboardId)]

    def draw(self, window: pygame.Surface, pendingMove: Optional[BallGroup]):
        for tube in self.tubes:
            tube.draw(window, pendingMove)
    
    def tryGetAutoMove(self, source: Tube) -> Optional[Tube]:
        emptyValidMove = None
        for t in self.tubes:
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
        for source in self.tubes:
            if source.get_isEmpty():
                continue
            sourcePeek = source.peek()
            for target in self.tubes:
                if target is not source and target.canAddBallGroup(sourcePeek):
                    if firstValidMove is None:
                        firstValidMove = source
                    if source is existingMove:
                        hitExistingMove = True
                    elif hitExistingMove:
                        return source
        return firstValidMove

    def tryFindTubeByPosition(self, position: Tuple[int,int]) -> Optional[Tube]:
        for t in self.tubes:
            if t.rect.collidepoint(position):
                return t
        return None
    
    def numEmptyTubes(self) -> int:
        return sum(1 for t in self.tubes if t.get_isEmpty())

    @staticmethod
    def interpolatePosition(start: Tuple[float,float], end: Tuple[float,float], progress: float) -> Tuple[float,float]:
        return start[0] + (end[0]-start[0])*progress, start[1] + (end[1]-start[1])*progress

    @staticmethod
    def interpolate(waypoints: list[Tuple[float, float]]) -> Callable[[float], Tuple[float,float]]:
        totalLength = -1
        lengths: list[float] = list()
        lastWaypoint = [0,0]
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
            totalLengthSoFar = 0
            while totalLengthSoFar < progress * totalLength:
                totalLengthSoFar += lengths[index]
                index += 1
            # index is the next waypoint - we're between waypoints[index-1] and waypoints[index]
            priorWaypointDistance = 0
            for i in range(index-1): priorWaypointDistance += lengths[i]
            progressBetweenPoints = (totalLength*progress - priorWaypointDistance)/lengths[index-1]
            x = waypoints[index-1][0] + (waypoints[index][0] - waypoints[index-1][0])*progressBetweenPoints
            y = waypoints[index-1][1] + (waypoints[index][1] - waypoints[index-1][1])*progressBetweenPoints
            return x,y
        return interpolation

    def animateSelection(self, newSelection: Optional[Tube], oldSelection: Optional[Tube]) -> None:
        # background = pygame.Surface(self.__window.get_size())
        # newSelectionGroup = None if newSelection is None else newSelection.pop()
        # oldSelectionGroup = None if oldSelection is None else oldSelection.pop()
        # self.draw(background, None)
        # if newSelection is not None:
        #     newSelection.push(newSelectionGroup)  # type: ignore
        # if oldSelectionGroup is not None:
        #     oldSelection.push(oldSelectionGroup)  # type: ignore
        # newSelectionImage = None
        # newSelectionTopLeftStart = 0,0
        # newSelectionTopLeftEnd = 0,0
        # if newSelection:
        #     balls = newSelection.peek()
        #     newSelectionImage = pygame.surface.Surface((Drawing.CircleRadius*2, Drawing.CircleRadius*2*balls.count + Drawing.CircleVerticalSpacing*(balls.count-1)), pygame.SRCALPHA)
        #     for i in range(balls.count):
        #         newSelectionImage.blit(Drawing.BallImagesHighlighted[balls.color], (0, i*(Drawing.CircleRadius*2+Drawing.CircleVerticalSpacing)))
        #     index = self.tubes.index(newSelection)
        #     ccBefore = Drawing.getCircleCenter(newSelection.__emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=False)
        #     ccAfter = Drawing.getCircleCenter(newSelection.__emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=True)
        #     newSelectionTopLeftStart = ccBefore[0] - Drawing.CircleRadius, ccBefore[1] - Drawing.CircleRadius
        #     newSelectionTopLeftEnd = ccAfter[0] - Drawing.CircleRadius, ccAfter[1] - Drawing.CircleRadius
        # oldSelectionImage = None
        # oldSelectionTopLeftStart = 0,0
        # oldSelectionTopLeftEnd = 0,0
        # if oldSelection:
        #     balls = oldSelection.peek()
        #     oldSelectionImage = pygame.surface.Surface((Drawing.CircleRadius*2, Drawing.CircleRadius*2*balls.count + Drawing.CircleVerticalSpacing*(balls.count-1)), pygame.SRCALPHA)
        #     for i in range(balls.count):
        #         oldSelectionImage.blit(Drawing.BallImages[balls.color], (0, i*(Drawing.CircleRadius*2+Drawing.CircleVerticalSpacing)))
        #     index = self.tubes.index(oldSelection)
        #     ccBefore = Drawing.getCircleCenter(oldSelection.__emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=True)
        #     ccAfter = Drawing.getCircleCenter(oldSelection.__emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=False)
        #     oldSelectionTopLeftStart = ccBefore[0] - Drawing.CircleRadius, ccBefore[1] - Drawing.CircleRadius
        #     oldSelectionTopLeftEnd = ccAfter[0] - Drawing.CircleRadius, ccAfter[1] - Drawing.CircleRadius

        # startTime = time.time()
        # animationDuration = .1 # seconds
        # progress = 0
        # while progress < 1:
        #     progress = (time.time() - startTime) / animationDuration
        #     if progress >= 1:
        #         progress = 1

        #     self.__window.blit(background, (0,0))
        #     if newSelectionImage:
        #         self.__window.blit(newSelectionImage, TubeSet.interpolatePosition(newSelectionTopLeftStart, newSelectionTopLeftEnd, progress))
        #     if oldSelectionImage:
        #         self.__window.blit(oldSelectionImage, TubeSet.interpolatePosition(oldSelectionTopLeftStart, oldSelectionTopLeftEnd, progress))
        #     pygame.display.flip()
        return None

    def animateMove(self, source: Tube, target: Tube, moving: BallGroup, sourceIsSelected: bool) -> None:
        # background = pygame.surface.Surface(self.__window.get_size())
        # self.draw(background, None)
        # sourceIndex = self.tubes.index(source)
        # sourceRow = sourceIndex // Drawing.TubesPerRow
        # sourceColumn = sourceIndex % Drawing.TubesPerRow
        # targetIndex = self.tubes.index(target)
        # targetRow = targetIndex // Drawing.TubesPerRow
        # targetColumn = targetIndex % Drawing.TubesPerRow
        # interpolatorFunctions: list[Callable[[float], Tuple[float,float]]] = []
        # topOfSourceTube = Drawing.getCircleCenter(0, sourceColumn, sourceRow, sourceIsSelected)
        # topOfSourceTube = topOfSourceTube[0], topOfSourceTube[1] - Drawing.CircleRadius*2 + Drawing.CircleVerticalSpacing
        # topOfTargetTube = Drawing.getCircleCenter(0, targetColumn, targetRow, False)
        # topOfTargetTube = topOfTargetTube[0], topOfTargetTube[1] - Drawing.CircleRadius*2 + Drawing.CircleVerticalSpacing
        # for i in range(moving.count):
        #     start = Drawing.getCircleCenter(source.__emptySlots - moving.count + i, sourceColumn, sourceRow, sourceIsSelected)
        #     end = Drawing.getCircleCenter(target.__emptySlots - 1 - i, targetColumn, targetRow, False)
        #     interpolatorFunctions.append( \
        #         TubeSet.interpolate( [start,topOfSourceTube,topOfTargetTube,end] ))

        # startTime = time.time()
        # animationDuration = .25 # seconds
        # progress = 0
        # while progress < 1:
        #     progress = (time.time() - startTime) / animationDuration
        #     if progress >= 1:
        #         progress = 1

        #     self.__window.blit(background, (0,0))
        #     for f in interpolatorFunctions:
        #         center = f(progress)
        #         topLeft = center[0] - Drawing.CircleRadius, center[1] - Drawing.CircleRadius
        #         self.__window.blit(Drawing.BallImages[moving.color], topLeft)
        #     pygame.display.flip()
        return None

    def setPendingMove(self, selectedTube: Optional[Tube]) -> None:
        if selectedTube is not self.pendingMove:
            self.animateSelection(selectedTube, self.pendingMove)
            self.pendingMove = selectedTube

    def doMove(self, selectedTube: Tube):
        if self.pendingMove is selectedTube:
            self.setPendingMove(None)
        elif self.pendingMove is None and selectedTube is not None and not selectedTube.get_isEmpty():
            self.setPendingMove(selectedTube)
        elif self.pendingMove is not None and selectedTube is not None and selectedTube.canAddBallGroup(self.pendingMove.peek()):
            self.undoStack.append(MoveRecord(self.pendingMove, selectedTube))
            self.redoStack.clear()
            moving = self.pendingMove.pop()
            self.animateMove(self.pendingMove, selectedTube, moving, True)
            selectedTube.push(moving)
            self.pendingMove = None
        elif not selectedTube.get_isEmpty():
            self.setPendingMove(selectedTube)

    def undo(self):
        if not self.undoStack:
            return
        moveToUndo = self.undoStack.pop()
        moving = BallGroup(color = moveToUndo.target.peek().color, count = moveToUndo.count)
        moveToUndo.target.removeBalls(moveToUndo.count)
        self.animateMove(moveToUndo.target, moveToUndo.source, moving, False)
        moveToUndo.source.push(moving)
        self.redoStack.append(moveToUndo)

    def redo(self):
        if not self.redoStack:
            return
        moveToRedo = self.redoStack.pop()
        moving = BallGroup(color = moveToRedo.source.peek().color, count = moveToRedo.count)
        moveToRedo.source.removeBalls(moveToRedo.count)
        self.animateMove(moveToRedo.source, moveToRedo.target, moving, False)
        moveToRedo.target.push(moving)
        self.undoStack.append(moveToRedo)

    def update(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.setPendingMove(None)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.setPendingMove(self.tryFindMove(self.pendingMove))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL and event.mod & pygame.KMOD_SHIFT:
                self.setPendingMove(None)
                oldEmptyCount = self.numEmptyTubes()
                while any(self.undoStack) and self.numEmptyTubes() <= oldEmptyCount:
                    self.undo()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL:
                self.setPendingMove(None)
                self.undo()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_y and event.mod & pygame.KMOD_CTRL:
                self.setPendingMove(None)
                self.redo()
            elif event.type == pygame.KEYDOWN and (self.isTubeKeyboardShortcut(event.key) or event.key == pygame.K_SPACE):
                if event.key == pygame.K_SPACE:
                    selectedTube = None if self.pendingMove is None else self.tryGetAutoMove(self.pendingMove)
                else:
                    selectedTube = self.getTubeForKeyStroke(event.key)

                if selectedTube is not None:
                    self.doMove(selectedTube)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                (x,y) = event.pos
                selectedTube: Optional[Tube] = self.tryFindTubeByPosition((x,y))
                if selectedTube is not None:
                    self.doMove(selectedTube)
        self.draw(self.__window, None if self.pendingMove is None else self.pendingMove.peek())