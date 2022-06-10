
from array import array
import math
import random
import time
from typing import Callable, Optional, Tuple

import pygame
from BallGroup import BallGroup
from Drawing import Drawing
from Tube import Tube


class TubeSet:
    tubes: list[Tube]

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

    def __init__(self, numTubes: int, numFreeTubes: int, depth: int):
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

        self.tubes = []
        for i in range(numTubes):
            newTube = Tube(depth)
            for j in range(depth):
                newTube.push(BallGroup(color=a[i*depth+j], count=1))
            self.tubes.append(newTube)

        for i in range(numFreeTubes):
            self.tubes.append(Tube(depth))

    # Tests to see if the top color block can be moved and, if so, to which
    # tubes could it be added.
    def canMove(self, slot: Tube) -> list[Tube]:
        if slot.get_isEmpty(): return list()
        return list(filter(lambda t: t != slot and slot.canAddBallGroup(slot.peek()), self.tubes))

    def isTubeKeyboardShortcut(self, keyboardId: int) -> bool:
        return keyboardId in TubeSet.__tubeKeys

    def getTubeForKeyStroke(self, keyboardId: int) -> Tube:
        return self.tubes[TubeSet.__tubeKeys.index(keyboardId)]

    def draw(self, window: pygame.surface.Surface, pendingMove: Optional[BallGroup]):
        rowWidth = Drawing.TubesPerRow
        row = 0
        column = 0
        for tube in self.tubes:
            tube.draw(window, row, column, pendingMove, self.__keyboardHintCharacters[row*rowWidth+column])
            column += 1
            if column == rowWidth:
                column = 0
                row += 1
    
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
        (x,y) = position
        tubesLeft: float = Drawing.TubeMarginLeft - Drawing.TubeHorizontalSpacing//2
        tubesRight = Drawing.TubeMarginLeft + (Drawing.TubesPerRow-1)*Drawing.CircleRadius*2 + Drawing.TubesPerRow*Drawing.TubeHorizontalSpacing
        tubeHeight = Drawing.BallsPerTube*Drawing.CircleRadius*2 + (Drawing.BallsPerTube-1)*Drawing.CircleVerticalSpacing
        tubeTop = Drawing.TubeMarginTop - Drawing.TubeMarginAroundBalls
        if x < tubesLeft or x > tubesRight:
            return None
        column:int = math.floor((x - tubesLeft)/(Drawing.CircleRadius*2 + Drawing.TubeHorizontalSpacing))
        for row in range(4):
            rowTop = tubeTop+row*(tubeHeight+Drawing.TubeVerticalSpacing)
            rowBottom = rowTop + tubeHeight + 2*Drawing.TubeMarginAroundBalls
            if y >= rowTop and y <= rowBottom:
                index = row*Drawing.TubesPerRow+column
                return self.tubes[index] if index < len(self.tubes) else None
        return None
    
    def numEmptyTubes(self) -> int:
        return sum(1 for t in self.tubes if t.get_isEmpty())

    @staticmethod
    def interpolatePosition(start: Tuple[float,float], end: Tuple[float,float], progress: float) -> Tuple[float,float]:
        return start[0] + (end[0]-start[0])*progress, start[1] + (end[1]-start[1])*progress

    def animateSelection(self, window: pygame.surface.Surface, newSelection: Optional[Tube], oldSelection: Optional[Tube]) -> None:
        background = pygame.surface.Surface(window.get_size())
        newSelectionGroup = None if newSelection is None else newSelection.pop()
        oldSelectionGroup = None if oldSelection is None else oldSelection.pop()
        self.draw(background, None)
        if newSelection is not None:
            newSelection.push(newSelectionGroup)  # type: ignore
        if oldSelectionGroup is not None:
            oldSelection.push(oldSelectionGroup)  # type: ignore
        newSelectionImage = None
        newSelectionTopLeftStart = 0,0
        newSelectionTopLeftEnd = 0,0
        if newSelection:
            balls = newSelection.peek()
            newSelectionImage = pygame.surface.Surface((Drawing.CircleRadius*2, Drawing.CircleRadius*2*balls.count + Drawing.CircleVerticalSpacing*(balls.count-1)), pygame.SRCALPHA)
            for i in range(balls.count):
                newSelectionImage.blit(Drawing.BallImagesHighlighted[balls.color], (0, i*(Drawing.CircleRadius*2+Drawing.CircleVerticalSpacing)))
            index = self.tubes.index(newSelection)
            ccBefore = Drawing.getCircleCenter(newSelection.emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=False)
            ccAfter = Drawing.getCircleCenter(newSelection.emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=True)
            newSelectionTopLeftStart = ccBefore[0] - Drawing.CircleRadius, ccBefore[1] - Drawing.CircleRadius
            newSelectionTopLeftEnd = ccAfter[0] - Drawing.CircleRadius, ccAfter[1] - Drawing.CircleRadius
        oldSelectionImage = None
        oldSelectionTopLeftStart = 0,0
        oldSelectionTopLeftEnd = 0,0
        if oldSelection:
            balls = oldSelection.peek()
            oldSelectionImage = pygame.surface.Surface((Drawing.CircleRadius*2, Drawing.CircleRadius*2*balls.count + Drawing.CircleVerticalSpacing*(balls.count-1)), pygame.SRCALPHA)
            for i in range(balls.count):
                oldSelectionImage.blit(Drawing.BallImages[balls.color], (0, i*(Drawing.CircleRadius*2+Drawing.CircleVerticalSpacing)))
            index = self.tubes.index(oldSelection)
            ccBefore = Drawing.getCircleCenter(oldSelection.emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=True)
            ccAfter = Drawing.getCircleCenter(oldSelection.emptySlots, index % Drawing.TubesPerRow, index // Drawing.TubesPerRow, isPendingMove=False)
            oldSelectionTopLeftStart = ccBefore[0] - Drawing.CircleRadius, ccBefore[1] - Drawing.CircleRadius
            oldSelectionTopLeftEnd = ccAfter[0] - Drawing.CircleRadius, ccAfter[1] - Drawing.CircleRadius

        startTime = time.time()
        animationDuration = .1 # seconds
        progress = 0
        while progress < 1:
            progress = (time.time() - startTime) / animationDuration
            if progress >= 1:
                progress = 1

            window.blit(background, (0,0))
            if newSelectionImage:
                window.blit(newSelectionImage, TubeSet.interpolatePosition(newSelectionTopLeftStart, newSelectionTopLeftEnd, progress))
            if oldSelectionImage:
                window.blit(oldSelectionImage, TubeSet.interpolatePosition(oldSelectionTopLeftStart, oldSelectionTopLeftEnd, progress))
            pygame.display.flip()
        return None

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

    def animateMove(self, window: pygame.surface.Surface, source: Tube, target: Tube, moving: BallGroup, sourceIsSelected: bool) -> None:
        background = pygame.surface.Surface(window.get_size())
        self.draw(background, None)
        sourceIndex = self.tubes.index(source)
        sourceRow = sourceIndex // Drawing.TubesPerRow
        sourceColumn = sourceIndex % Drawing.TubesPerRow
        targetIndex = self.tubes.index(target)
        targetRow = targetIndex // Drawing.TubesPerRow
        targetColumn = targetIndex % Drawing.TubesPerRow
        interpolatorFunctions: list[Callable[[float], Tuple[float,float]]] = []
        topOfSourceTube = Drawing.getCircleCenter(0, sourceColumn, sourceRow, sourceIsSelected)
        topOfSourceTube = topOfSourceTube[0], topOfSourceTube[1] - Drawing.CircleRadius*2 + Drawing.CircleVerticalSpacing
        topOfTargetTube = Drawing.getCircleCenter(0, targetColumn, targetRow, False)
        topOfTargetTube = topOfTargetTube[0], topOfTargetTube[1] - Drawing.CircleRadius*2 + Drawing.CircleVerticalSpacing
        for i in range(moving.count):
            start = Drawing.getCircleCenter(source.emptySlots - moving.count + i, sourceColumn, sourceRow, sourceIsSelected)
            end = Drawing.getCircleCenter(target.emptySlots - 1 - i, targetColumn, targetRow, False)
            interpolatorFunctions.append( \
                TubeSet.interpolate( [start,topOfSourceTube,topOfTargetTube,end] ))

        startTime = time.time()
        animationDuration = .25 # seconds
        progress = 0
        while progress < 1:
            progress = (time.time() - startTime) / animationDuration
            if progress >= 1:
                progress = 1

            window.blit(background, (0,0))
            for f in interpolatorFunctions:
                center = f(progress)
                topLeft = center[0] - Drawing.CircleRadius, center[1] - Drawing.CircleRadius
                window.blit(Drawing.BallImages[moving.color], topLeft)
            pygame.display.flip()
        return None
