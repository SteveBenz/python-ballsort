from array import array
from math import ceil, floor
import random
import time
from typing import Optional, Tuple
import pygame

# Gotta do this first:
#  py -m pip install pygame
#
# If errors, maybe do this first:
#  py -m pip uninstall pygame

# TODO:
# Animated movement
# Better like-colors highlight
# Save State
# New Game
# Detect Win and Loss

pygame.init()

white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
brown = (255, 255, 0)
purple = (255, 0, 255)
black = (0, 0, 0)

keyboardHintCharacters = (
    ('1', '2', '3', '4', '5', 'q', 'w', 'e', 'r', 't'),
    ('a', 's', 'd', 'f', 'g', 'z', 'x', 'c', 'v', 'b'))

pygame.font.init()
arialFont = pygame.font.SysFont('arial', 16)

class GameColors:
    TubeBackground = (50,50,50)
    ValidTargetTubeBackground = (70,70,70)
    WindowBackground = (0,0,0)
    KeyboardHintNormal = (128, 128, 128)
    KeyboardHintCanMoveTo = (255, 255, 255)

class Drawing:
    CircleRadius: float = 10
    MatchCircleRadius: float = 2
    TubeMarginTop: float = 50
    TubeMarginLeft: float = CircleRadius
    CircleVerticalSpacing: float = CircleRadius//5
    TubeHorizontalSpacing: float = CircleRadius + CircleRadius//2
    TubeVerticalSpacing: float = CircleRadius*3
    TubeMarginAroundBalls: float = 3
    ScreenWidth: float = 650
    ScreenHeight: float = 700
    BallsPerTube: int = 6
    FullTubes: int = 16
    EmptyTubes: int = 3
    TubesPerRow: int = 10
    BallImages: list[pygame.Surface] = []

    BallColors = (
        (255,105,180), # Hot Pink
        (220, 20, 60), # crimson
        (255, 140, 0), # orange
        (255, 255, 0), # yellow
        (160, 82, 45), # sienna
        (222, 184, 135), # burly wood
        (50, 205, 50), # lime green
        (0, 206, 209), # dark turquoise
        (0, 0, 255), # medium blue
        (0, 191, 255), # deep sky blue
        (147, 112, 219), # medium purple
        (255, 255, 255), # white
        (47, 79, 79), # dark slate
        (188, 143, 143), # rosy brown
        (0, 100, 0), # dark green
        (169, 169, 169), # dark gray
    )


    @staticmethod
    def resize(w: float, h: float) -> None:
        # TubeMarginLeft (1)
        # |  Circles (2)
        # |  |  TubeHorizontalSpacing (1.5)
        # 2 (for the margins)
        # (n-1) * 1.5  (for the spaces between)
        # 2*n for the tubes themselves

        circleRadiusBasedOnWidth = w / ( 2*Drawing.TubesPerRow + 2 +(Drawing.TubesPerRow-1)*1.5)

        nRows:int = ceil((Drawing.FullTubes+Drawing.EmptyTubes)/(Drawing.TubesPerRow))
        # 5*            margin top
        # (nRows-1)*3   between rows
        # nRows*ballsPerTube*2  circles
        # nRows*(ballsPerTube-1)*.2  spacing between balls
        # 1*            margin bottom

        circleRadiusBasedOnHeight = h / (3+(nRows-1)*3 + nRows*Drawing.BallsPerTube*2 + nRows*(Drawing.BallsPerTube-1)*.2 + 3)

        Drawing.CircleRadius = min(circleRadiusBasedOnWidth, circleRadiusBasedOnHeight)
        Drawing.TubeMarginTop = Drawing.CircleRadius*3
        Drawing.MatchCircleRadius = Drawing.CircleRadius / 5
        Drawing.TubeMarginLeft = Drawing.CircleRadius
        Drawing.CircleVerticalSpacing = Drawing.CircleRadius / 5
        Drawing.TubeHorizontalSpacing = Drawing.CircleRadius * 1.5
        Drawing.TubeVerticalSpacing = Drawing.CircleRadius * 3
        Drawing.TubeMarginAroundBalls = Drawing.CircleRadius * .3

        Drawing.BallImages.clear()
        for i in range(Drawing.FullTubes):
            x = Drawing.CircleRadius
            y = Drawing.CircleRadius
            ballImage = pygame.Surface((2*Drawing.CircleRadius,2*Drawing.CircleRadius), pygame.SRCALPHA)
            if i % 5 == 0:
                pygame.draw.circle(ballImage, Drawing.BallColors[i], [x,y], Drawing.CircleRadius)
            elif i % 5 == 1:
                pygame.draw.rect(ballImage, Drawing.BallColors[i], pygame.Rect(x-Drawing.CircleRadius,y-Drawing.CircleRadius,2*Drawing.CircleRadius,2*Drawing.CircleRadius))
            elif i % 5 == 2:
                pygame.draw.polygon(ballImage, Drawing.BallColors[i],
                    [(x,y-Drawing.CircleRadius), 
                    (x-Drawing.CircleRadius,y),
                    (x,y+Drawing.CircleRadius),
                    (x+Drawing.CircleRadius,y)])
            elif i % 5 == 3:
                pygame.draw.polygon(ballImage, Drawing.BallColors[i],
                    [(x,y-Drawing.CircleRadius), 
                    (x-Drawing.CircleRadius,y+Drawing.CircleRadius),
                    (x+Drawing.CircleRadius,y+Drawing.CircleRadius)])
            elif i % 5 == 4:
                pygame.draw.polygon(ballImage, Drawing.BallColors[i],
                    [(x-Drawing.CircleRadius,y-Drawing.CircleRadius),
                    (x+Drawing.CircleRadius,y-Drawing.CircleRadius),
                    (x,y+Drawing.CircleRadius)])
            Drawing.BallImages.append(ballImage)
    
    @staticmethod
    def getTubeRect(column: int, row: int) -> pygame.Rect:
        tubeCenter = Drawing.TubeMarginLeft + column*(Drawing.CircleRadius*2 + Drawing.TubeHorizontalSpacing) + Drawing.CircleRadius
        tubeTotalHeight = Drawing.BallsPerTube*Drawing.CircleRadius*2 + (Drawing.BallsPerTube-1)*Drawing.CircleVerticalSpacing
        tubeTop = Drawing.TubeMarginTop + row*(tubeTotalHeight + Drawing.TubeVerticalSpacing)
        return pygame.Rect(tubeCenter - Drawing.CircleRadius - Drawing.TubeMarginAroundBalls,
            tubeTop - Drawing.TubeMarginAroundBalls,
            (Drawing.CircleRadius + Drawing.TubeMarginAroundBalls)*2,
            tubeTotalHeight + 2*Drawing.TubeMarginAroundBalls)

    @staticmethod
    def getCircleCenter(ball: int, column: int, row: int, isPendingMove: bool) -> Tuple[float,float]:
        r = Drawing.getTubeRect(column, row)
        x = r.left + Drawing.TubeMarginAroundBalls + Drawing.CircleRadius
        y = r.top + Drawing.TubeMarginAroundBalls + ball*(2*Drawing.CircleRadius + Drawing.CircleVerticalSpacing) + Drawing.CircleRadius
        if isPendingMove:
            y -= Drawing.CircleRadius
        return x,y
    
class BallGroup:
    color: int
    count: int

    def __init__(self, color: int, count: int):
        self.color = color
        self.count = count

class Tube:
    emptySlots: int
    ballGroups: list[BallGroup]

    def __init__(self, depth: int):
        self.emptySlots = depth
        self.ballGroups = list()

    def peek(self) -> BallGroup:
        return self.ballGroups[0]

    def pop(self) -> BallGroup:
        r = self.ballGroups.pop(0)
        self.emptySlots += r.count
        return r

    def removeBalls(self, count: int) -> None:
        if self.ballGroups[0].count == count:
            self.ballGroups.pop(0)
        else:
            self.ballGroups[0].count -= count
        self.emptySlots += count

    def get_isEmpty(self) -> bool:
        return not any(self.ballGroups)

    def get_isComplete(self) -> bool:
        return self.emptySlots == Drawing.BallsPerTube or (len(self.ballGroups) == 1 and self.emptySlots == 0)

    def canAddBallGroup(self, group: BallGroup) -> bool:
        if self.emptySlots < group.count: return False
        if len(self.ballGroups) == 0: return True
        return self.ballGroups[0].color == group.color

    def push(self, group: BallGroup) -> None:
        if len(self.ballGroups) > 0 and self.ballGroups[0].color == group.color:
            self.ballGroups[0].count += group.count
        else:
            self.ballGroups.insert(0, group)
        self.emptySlots -= group.count

    def draw(self, window: pygame.surface.Surface, row: int, column: int, pendingMove: Optional[BallGroup]) -> None:
        tubeCanBeNextMove = pendingMove != None and self.canAddBallGroup(pendingMove)
        background = GameColors.ValidTargetTubeBackground if tubeCanBeNextMove else GameColors.TubeBackground
        pygame.draw.rect(window, background, Drawing.getTubeRect(column, row))

        ballNumber = self.emptySlots
        for group in self.ballGroups:
            for _ in range(group.count):
                image = Drawing.BallImages[group.color]
                center = Drawing.getCircleCenter(ballNumber, column, row, group is pendingMove)
                ballNumber += 1
                window.blit(image, (center[0] - Drawing.CircleRadius, center[1] - Drawing.CircleRadius))

        hintColor = GameColors.KeyboardHintCanMoveTo if tubeCanBeNextMove else GameColors.KeyboardHintNormal
        hintImage = arialFont.render(keyboardHintCharacters[row][column], True, hintColor)
        hintImageRect = hintImage.get_rect()
        topCircleCenter = Drawing.getCircleCenter(0, column, row, (not self.get_isEmpty()) and pendingMove == self.peek())
        window.blit(hintImage,
            (topCircleCenter[0] - hintImageRect.width/2, topCircleCenter[1] - Drawing.CircleVerticalSpacing - Drawing.CircleRadius - hintImageRect.height,
            hintImageRect.width, hintImageRect.height))

class TubeSet:
    tubes: list[Tube]

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

    def draw(self, window: pygame.surface.Surface, pendingMove: Optional[BallGroup]):
        rowWidth = Drawing.TubesPerRow
        row = 0
        column = 0
        for tube in self.tubes:
            tube.draw(window, row, column, pendingMove)
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
    
    def tryFindMove(self) -> Optional[Tube]:
        for source in self.tubes:
            if source.get_isEmpty():
                continue
            sourcePeek = source.peek()
            for target in self.tubes:
                if target is not source and target.canAddBallGroup(sourcePeek):
                    return source
        return None

    def tryFindTubeByPosition(self, position: Tuple[int,int]) -> Optional[Tube]:
        (x,y) = position
        tubesLeft: float = Drawing.TubeMarginLeft - Drawing.TubeHorizontalSpacing//2
        tubesRight = Drawing.TubeMarginLeft + (Drawing.TubesPerRow-1)*Drawing.CircleRadius*2 + Drawing.TubesPerRow*Drawing.TubeHorizontalSpacing
        tubeHeight = Drawing.BallsPerTube*Drawing.CircleRadius*2 + (Drawing.BallsPerTube-1)*Drawing.CircleVerticalSpacing
        tubeTop = Drawing.TubeMarginTop - Drawing.TubeMarginAroundBalls
        if x < tubesLeft or x > tubesRight:
            return None
        column:int = floor((x - tubesLeft)/(Drawing.CircleRadius*2 + Drawing.TubeHorizontalSpacing))
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
                newSelectionImage.blit(Drawing.BallImages[balls.color], (0, i*(Drawing.CircleRadius*2+Drawing.CircleVerticalSpacing)))
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

class MoveRecord:
    source: Tube
    target: Tube
    count: int

    def __init__(self, source: Tube, target: Tube):
        sourceTop = source.peek()
        self.count = sourceTop.count
        self.source = source
        self.target = target


window = pygame.display.set_mode((Drawing.ScreenWidth, Drawing.ScreenHeight), pygame.RESIZABLE)
pygame.display.set_caption("Ball Sort")
pygame.display.set_icon(pygame.image.load("icon.png"))
pygame.display.update()

Drawing.resize(Drawing.ScreenWidth, Drawing.ScreenHeight)

tubeKeys = (
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
    pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t,
    pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g,
    pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b
)

tubes = TubeSet(Drawing.FullTubes, Drawing.EmptyTubes, Drawing.BallsPerTube)
source: Optional[Tube] = None
closing = False
undoStack: list[MoveRecord] = []
redoStack: list[MoveRecord] = []
pendingMove: Optional[Tube] = None

def setPendingMove(selectedTube: Optional[Tube]) -> None:
    global pendingMove
    if selectedTube is not pendingMove:
        tubes.animateSelection(window, selectedTube, pendingMove)
        pendingMove = selectedTube


def doMove(selectedTube: Tube):
    global pendingMove
    if pendingMove is selectedTube:
        setPendingMove(None)
    elif pendingMove is None and selectedTube is not None and not selectedTube.get_isEmpty():
        setPendingMove(selectedTube)
    elif pendingMove is not None and selectedTube is not None and selectedTube.canAddBallGroup(pendingMove.peek()):
        undoStack.append(MoveRecord(pendingMove, selectedTube))
        redoStack.clear()
        selectedTube.push(pendingMove.pop())
        pendingMove = None
    elif not selectedTube.get_isEmpty():
        setPendingMove(selectedTube)

def undo():
    moveToUndo = undoStack.pop()
    moveToUndo.source.push(BallGroup(color = moveToUndo.target.ballGroups[0].color, count = moveToUndo.count))
    moveToUndo.target.removeBalls(moveToUndo.count)
    redoStack.append(moveToUndo)

# main loop
while not closing:
    # event handling, gets all event from the event queue
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            closing = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            setPendingMove(None)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            setPendingMove(tubes.tryFindMove())
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL and event.mod & pygame.KMOD_SHIFT:
            oldEmptyCount = tubes.numEmptyTubes()
            while any(undoStack) and tubes.numEmptyTubes() <= oldEmptyCount:
                undo()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL:
            if any(undoStack): undo()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_y and event.mod & pygame.KMOD_CTRL:
            if any(redoStack):
                moveToRedo = redoStack.pop()
                moveToRedo.target.push(BallGroup(color = moveToRedo.source.ballGroups[0].color, count = moveToRedo.count))
                moveToRedo.source.removeBalls(moveToRedo.count)
                undoStack.append(moveToRedo)
        elif event.type == pygame.KEYDOWN and (event.key in tubeKeys or event.key == pygame.K_SPACE):
            if event.key == pygame.K_SPACE:
                selectedTube = None if pendingMove is None else tubes.tryGetAutoMove(pendingMove)
            else:
                selectedTube = tubes.tubes[tubeKeys.index(event.key)]

            if selectedTube is not None:
                doMove(selectedTube)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            (x,y) = event.pos
            selectedTube: Optional[Tube] = tubes.tryFindTubeByPosition((x,y))
            if selectedTube is not None:
                doMove(selectedTube)

        elif event.type == pygame.VIDEORESIZE:
            Drawing.resize(event.w, event.h)

    window.fill(black)

    tubes.draw(window, None if pendingMove is None else pendingMove.peek())
    pygame.display.flip()

