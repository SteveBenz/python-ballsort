import math
from random import randint, randrange
import random
import time
from typing import Any, Callable, Iterable, Optional, Tuple

import pygame
from BallGroup import BallGroup
from GameColors import GameColors
from MoveRecord import MoveRecord
from Tube import Tube
from pygame.surface import Surface
from pygame.rect import Rect
from pygame.event import Event


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

    def __init__(self, window: Surface, rect: Rect):
        self.__window = window
        self.__rect = rect
        self.__tubes: list[Tube] = []
        self.__undoStack: list[MoveRecord] = []
        self.__redoStack: list[MoveRecord] = []
        self.__pendingMove: Optional[Tube] = None

    def newGame(self, numTubes: int, numColors: int, ballsPerTubes: int) -> None:
        a: list[int] = []
        for t in self.__tubes:
            a += [-1 for _ in range(t.emptySlots)]
            while not t.isEmpty:
                g = t.pop(None)
                a += [g.color for _ in range(g.count)]
        self.animateEraseGame(a)

        self.__createEmptyGame(numTubes, ballsPerTubes)
        a = [0]*numColors*ballsPerTubes
        td = numColors*ballsPerTubes
        for i in range(td):
            a[i] = i % numColors
        for i in range(td):
            swapWith = randint(i,td-1)
            if swapWith != i:
                h = a[i]
                a[i] = a[swapWith]
                a[swapWith] = h
        self.animateNewGame(a)
        for i in range(numColors):
            for j in range(ballsPerTubes):
                self.__tubes[i].push(BallGroup(color=a[i*ballsPerTubes+j], count=1))

    def loadGame(self, d: dict[str,Any]) -> None:
        ballsPerTube = d['ballsPerTube']
        batches: list[list[int]] = d['balls']
        self.__createEmptyGame(len(batches), ballsPerTube)
        for i in range(len(batches)):
            for color in batches[i]:
                self.__tubes[i].push(BallGroup(color=color, count=1))
        self.__undoStack = [self.__parseMoveRecord(r) for r in d['undoStack']]
        self.__redoStack = [self.__parseMoveRecord(r) for r in d['redoStack']]
    
    
    def __serializeMoveRecord(self, r: MoveRecord) -> dict[str,Any]:
        d: dict[str,Any] = dict()
        d['source'] = self.__tubes.index(r.source)
        d['target'] = self.__tubes.index(r.target)
        d['count'] = r.count
        return d

    def __parseMoveRecord(self, r: Any) -> MoveRecord:
        return MoveRecord(self.__tubes[r['source']], self.__tubes[r['target']], r['count'])

    def __createEmptyGame(self, numTubes: int, ballsPerTube: int) -> None:
        self.__undoStack = []
        self.__redoStack = []
        self.__pendingMove = None
        self.__depth = ballsPerTube
        self.__tubes = []
        i = 0
        for tubeRect in TubeSet.__getTubeLayout(self.__rect, numTubes, ballsPerTube):
            self.__tubes.append(Tube(self.__window, tubeRect, TubeSet.__keyboardHintCharacters[i], ballsPerTube))
            i += 1
    
    def serialize(self) -> dict[str,Any]:
        d: dict[str,Any] = dict()
        batches: list[list[int]] = []
        for t in self.__tubes:
            batches.append(t.serialize())
        d['balls'] = batches
        d['ballsPerTube'] = self.numBallsPerTube
        d['undoStack'] = [self.__serializeMoveRecord(s) for s in self.__undoStack]
        d['redoStack'] = [self.__serializeMoveRecord(s) for s in self.__redoStack]
        return d
    
    def reposition(self, rect: Rect) -> None:
        i = 0
        for l in TubeSet.__getTubeLayout(rect, len(self.__tubes), self.__depth):
            self.__tubes[i].rect = l
            i += 1
        self.__rect = rect

    @staticmethod
    def __getTubeLayout(rect: Rect, numTubes: int, numBalls: int) -> Iterable[Rect]:
        # Hard-coding to a two-row.  Better if we adjusted it based on the layout
        rows:int = 0
        width = 0
        height = 0
        columns = 0
        while True:
            r = rows+1
            c = (numTubes+1)//r
            (w,h) = Tube.getMaxUsableSize((rect.width / c, rect.height / r), numBalls)
            if w*h > width*height:
                (width,height,rows,columns) = (w,h,r,c)
            else:
                break

        # It'd be better if the extra space was distributed between rows and columns
        for i in range(numTubes):
            row = i // columns
            column = i % columns
            yield Rect(width*column + rect.left, height*row + rect.top, width, height)

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
            if t.isEmpty:
                if emptyValidMove is None:
                    emptyValidMove = t
            elif t.canAddBallGroup(source.peek()):
                return t
        return emptyValidMove
    
    def __getAllValidMoves(self) -> Iterable[Tube]:
        # First list out all the moves that don't target empty tubes
        hasAnyEmptyTubes: bool = False
        possibleEmptyTubeMoves: list[Tube] = []
        for source in self.__tubes:
            if source.isEmpty:
                hasAnyEmptyTubes = True
            else:
                sourcePeek = source.peek()
                if any(t for t in self.__tubes if t is not source and (not t.isEmpty) and t.canAddBallGroup(sourcePeek)):
                    yield source
                elif source.hasMoreThanOneColor:
                    possibleEmptyTubeMoves.append(source)
        if hasAnyEmptyTubes:
            for source in possibleEmptyTubeMoves:
                yield source
    
    def tryFindMove(self, existingMove: Optional[Tube]) -> Optional[Tube]:
        hitExistingMove = existingMove is None
        firstValidMove = None
        for possibleMove in self.__getAllValidMoves():
            if hitExistingMove:
                return possibleMove
            elif possibleMove is existingMove:
                hitExistingMove = True
            elif firstValidMove is None:
                firstValidMove = possibleMove
        return firstValidMove

    def tryFindTubeByPosition(self, position: Tuple[int,int]) -> Optional[Tube]:
        for t in self.__tubes:
            if t.rect.collidepoint(position):
                return t
        return None
    
    @property
    def numEmptyTubes(self) -> int:
        return sum(1 for t in self.__tubes if t.isEmpty)

    @property
    def numTotalTubes(self) -> int:
        return len(self.__tubes)

    @property
    def numBallsPerTube(self) -> int:
        return self.__depth

    @property
    def isWin(self) -> bool:
        for t in self.__tubes:
            if not t.isComplete:
                return False
        return True

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
    
    def makeSelectionAnimator(self, selection: Tube, isIncoming: bool) -> Callable[[float], Rect]:
        selectionGroup = selection.peek()
        topBallRectHigh = selection.getBallPosition(selection.emptySlots-.5)
        bottomBallRect = selection.getBallPosition(selection.emptySlots+selectionGroup.count-1)
        animationArea = topBallRectHigh.union(bottomBallRect)
        background = Surface(animationArea.size)

        _ = selection.pop(selectionGroup.count)
        selection.draw(
            canAddHighlight=False,
            isSourceHighlight=False,
            highlightedColor=selectionGroup.color)
        background.blit(self.__window, (0,0), animationArea)
        selection.push(selectionGroup)
        ballImage = selection.getBallImage(selectionGroup.color, isHighlighted=True)
        def animation(position: float) -> Rect:
            self.__window.blit(background, animationArea)
            for ballTubePosition in range(selection.emptySlots, selection.emptySlots+selectionGroup.count):
                target = selection.getBallPosition(ballTubePosition - .5*(position if isIncoming else 1-position))
                self.__window.blit(ballImage, target)
            return animationArea
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
            updateAreas: list[Rect] = []
            if newAnimation:
                updateAreas.append(newAnimation(progress))
            if oldAnimation:
                updateAreas.append(oldAnimation(progress))
            pygame.display.update(updateAreas)  # type: ignore   Looks like a pylance bug
            time.sleep(.01)

    def animateMove(self, source: Tube, target: Tube, moving: BallGroup, sourceIsSelected: bool) -> None:
        self.__pendingMove = None
        self.draw()
        background = Surface(self.__rect.size)
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
            time.sleep(.01)


    def animateNewGame(self, balls: list[int]) -> None:
        self.__window.fill(GameColors.WindowBackground, self.__rect)
        self.draw()
        screenSize = self.__window.get_size()
        background = Surface(screenSize)
        background.blit(self.__window, (0,0), self.__window.get_rect())

        startTime = time.time()

        timeSpentInTube = .5
        verticalSpeedInTube = (self.__tubes[0].getBallPosition(self.numBallsPerTube-1).top - self.__tubes[0].getBallPosition(-1).top) / timeSpentInTube
        def getArrivalTime(depth: int) -> float:
            return startTime + .25 + ((1 + self.numBallsPerTube - depth)/self.numBallsPerTube)*timeSpentInTube

        # What we want to animate is a condition where the balls arrive at the top of the tube
        # sequentially and thus don't overlap as they go down.
        class BallPlot:
            color: int
            startX: float
            startY: float
            topOfTubeX: float
            topOfTubeY: float
            finalX: float
            finalY: float
            arrivalTimeAtTopOfTube: float

            def getPositionAtTime(self, startTime: float, now: float) -> Tuple[float, float]:
                if now <= self.arrivalTimeAtTopOfTube:
                    transitPercentage = (now - startTime)/(self.arrivalTimeAtTopOfTube - startTime)
                    x = self.startX + (self.topOfTubeX - self.startX) * transitPercentage
                    y = self.startY + (self.topOfTubeY - self.startY) * transitPercentage
                    return x,y
                else:
                    y = self.topOfTubeY + verticalSpeedInTube * (now - self.arrivalTimeAtTopOfTube)
                    return self.topOfTubeX, min(y, self.finalY)

        plots: list[BallPlot] = []
        tube: int = 0
        depth: int = self.numBallsPerTube-1
        ballSize = self.__tubes[0].getBallImage(0,False).get_size()
        tubeArrivalTime = randrange(0,20)/10
        for color in balls:
            plot = BallPlot()
            plot.color = color
            startEdge = randint(0,3)
            if startEdge == 0:
                plot.startX = -ballSize[0]
                plot.startY = randint(-ballSize[1], screenSize[1])
            elif startEdge == 1:
                plot.startX = screenSize[0]
                plot.startY = randint(-ballSize[1], screenSize[1])
            elif startEdge == 2:
                plot.startX = randint(-ballSize[0], screenSize[0])
                plot.startY = -ballSize[1]
            else:
                plot.startX = randint(-ballSize[0], screenSize[0])
                plot.startY = screenSize[1]
            tubeTop = self.__tubes[tube].getBallPosition(-1)
            plot.topOfTubeX = tubeTop[0]
            plot.topOfTubeY = tubeTop[1]
            plot.arrivalTimeAtTopOfTube = getArrivalTime(depth) + tubeArrivalTime
            finalPosition = self.__tubes[tube].getBallPosition(depth)
            plot.finalX = finalPosition[0]
            plot.finalY = finalPosition[1]
            plots.append(plot)
            if depth == 0:
                depth = self.numBallsPerTube-1
                tubeArrivalTime = randrange(0,20)/10
                tube += 1
            else:
                depth -= 1

        numArrived = 0
        while numArrived < len(plots):
            self.__window.blit(background, (0,0))
            now = time.time()
            numArrived = 0
            for plot in plots:
                ballImage = self.__tubes[0].getBallImage(plot.color, isHighlighted=False)
                topLeft = plot.getPositionAtTime(startTime, now)
                self.__window.blit(ballImage, topLeft)
                if topLeft[0] == plot.finalX and topLeft[1] == plot.finalY:
                    numArrived += 1
            pygame.display.update()
            pygame.event.pump()
            time.sleep(.01)


    def animateEraseGame(self, balls: list[int]) -> None:
        self.__window.fill(GameColors.WindowBackground, self.__rect)
        self.draw()
        screenSize = self.__window.get_size()
        background = Surface(screenSize)
        background.blit(self.__window, (0,0), self.__window.get_rect())

        startTime = time.time()

        escapeMultiplier = 12

        # What we want to animate is a condition where the balls arrive at the top of the tube
        # sequentially and thus don't overlap as they go down.
        class BallPlot:
            color: int
            startX: float
            startY: float
            jiggleDuration: float
            dX: float
            dY: float

            def getPositionAtTime(self, startTime: float, now: float) -> Tuple[float, float]:
                elapsedTime = now - startTime
                if elapsedTime > self.jiggleDuration:
                    elapsedSinceJiggle = elapsedTime-self.jiggleDuration
                    return self.startX + self.dX * elapsedSinceJiggle * escapeMultiplier, self.startY + self.dY * elapsedSinceJiggle * escapeMultiplier
                else:
                    amplitude = math.sin(math.pi*6*elapsedTime/self.jiggleDuration)*elapsedTime/self.jiggleDuration
                    return self.startX + self.dX * amplitude, self.startY + self.dY * amplitude

        plots: list[BallPlot] = []
        tube: int = 0
        depth: int = 0
        ballSize = self.__tubes[0].getBallImage(0,False).get_size()
        for color in balls:
            if color >= 0:
                plot = BallPlot()
                plot.color = color
                startPosition = self.__tubes[tube].getBallPosition(depth)
                plot.startX = startPosition[0]
                plot.startY = startPosition[1]
                plot.dX = ballSize[0] * randrange(50,100)/100 * (randint(0,1)*2-1)
                plot.dY = ballSize[1] * randrange(50,100)/100 * (randint(0,1)*2-1)
                plot.jiggleDuration = .75 * randrange(50,100)/100
                plots.append(plot)
            depth += 1
            if depth == self.numBallsPerTube:
                depth = 0
                tube += 1
        
        def isOffScreen(x: float, y: float) -> bool:
            return x < -ballSize[0] or x > screenSize[0] or y < -ballSize[0] or y > screenSize[1]

        numArrived = 0
        while numArrived < len(plots):
            self.__window.blit(background, (0,0))
            now = time.time()
            numArrived = 0
            for plot in plots:
                ballImage = self.__tubes[0].getBallImage(plot.color, isHighlighted=False)
                topLeft = plot.getPositionAtTime(startTime, now)
                if isOffScreen(*topLeft):
                    numArrived += 1
                else:
                    self.__window.blit(ballImage, topLeft)
            pygame.event.pump()
            pygame.display.update()
            time.sleep(.01)

    def setPendingMove(self, selectedTube: Optional[Tube]) -> None:
        if selectedTube is not self.__pendingMove:
            self.animateSelection(selectedTube, self.__pendingMove)
            self.__pendingMove = selectedTube

    def doMove(self, selectedTube: Tube):
        def actuallyDoMove(source: Tube, target: Tube) -> None:
            self.__redoStack.clear()
            moving = source.pop(min(target.emptySlots, source.peek().count))
            self.animateMove(source, target, moving, True)
            target.push(moving)
            self.__pendingMove = None
            self.__undoStack.append(MoveRecord(source, target, moving.count))

        if self.__pendingMove and self.__pendingMove is selectedTube:
            target = self.tryGetAutoMove(self.__pendingMove)
            if target:
                actuallyDoMove(self.__pendingMove, target)
            else:
                self.setPendingMove(None)
        elif self.__pendingMove is None and selectedTube is not None and not selectedTube.isEmpty:
            self.setPendingMove(selectedTube)
        elif self.__pendingMove is not None and selectedTube is not None and selectedTube.canAddBallGroupPartial(self.__pendingMove.peek()):
            actuallyDoMove(self.__pendingMove, selectedTube)
        elif not selectedTube.isEmpty:
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


    def update(self, events: list[Event]) -> None:
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
