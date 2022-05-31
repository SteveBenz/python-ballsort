from array import array
import random
from typing import Optional, Tuple
import pygame

# Gotta do this first:
#  py -m pip install pygame
#
# If errors, maybe do this first:
#  py -m pip uninstall pygame

# TODO:
# Restart
# New Game
# Checkpoints - maybe ctrl+shift+z undoes until there's a free tube?
# Use different shapes as well as colors
# Save State
# Beep or something on bad move
# Detect Win and Loss
# Keyboard hint should light for similar colors on top?

pygame.init()

white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
brown = (255, 255, 0)
purple = (255, 0, 255)
black = (0, 0, 0)

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

keyboardHintCharacters = (
    ('1', '2', '3', '4', '5'),
    ('q', 'w', 'e', 'r', 't'),
    ('a', 's', 'd', 'f', 'g'),
    ('z', 'x', 'c', 'v', 'b'))

pygame.font.init()
arialFont = pygame.font.SysFont('arial', 16)

class GameColors:
    TubeBackground = (50,50,50)
    ValidTargetTubeBackground = (70,70,70)
    WindowBackground = (0,0,0)
    KeyboardHintNormal = (128, 128, 128)
    KeyboardHintCanMoveTo = (255, 255, 255)

class Spacing:
    CircleRadius = 10
    MatchCircleRadius = 2
    tubeMarginTop = 50
    TubeMarginLeft = CircleRadius
    CircleVerticalSpacing = CircleRadius//5
    TubeHorizontalSpacing = CircleRadius + CircleRadius//2
    TubeVerticalSpacing = CircleRadius*3
    TubeMarginAroundBalls = 3

    ScreenWidth = 650
    ScreenHeight = 700

class GameData:
    BallsPerTube = 6
    FullTubes = 16
    EmptyTubes = 3
    TubesPerRow = 5

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
        return self.emptySlots == GameData.BallsPerTube or (len(self.ballGroups) == 1 and self.emptySlots == 0)

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

    def draw(self, row: int, column: int, pendingMove: Optional['Tube']) -> None:
        tubeCenter = Spacing.TubeMarginLeft + column*(Spacing.CircleRadius*2 + Spacing.TubeHorizontalSpacing) + Spacing.CircleRadius
        tubeTotalHeight = GameData.BallsPerTube*Spacing.CircleRadius*2 + (GameData.BallsPerTube-1)*Spacing.CircleVerticalSpacing
        tubeTop = Spacing.tubeMarginTop + row*(tubeTotalHeight + Spacing.TubeVerticalSpacing)
        tubeCanBeNextMove = pendingMove != None and self.canAddBallGroup(pendingMove.peek())
        background = GameColors.ValidTargetTubeBackground if tubeCanBeNextMove else GameColors.TubeBackground
        pygame.draw.rect(window, background,
            pygame.Rect(tubeCenter - Spacing.CircleRadius - Spacing.TubeMarginAroundBalls,
            tubeTop - Spacing.TubeMarginAroundBalls,
            (Spacing.CircleRadius + Spacing.TubeMarginAroundBalls)*2,
            tubeTotalHeight + 2*Spacing.TubeMarginAroundBalls))

        x = tubeCenter
        y = tubeTop + self.emptySlots*(2*Spacing.CircleRadius + Spacing.CircleVerticalSpacing) + Spacing.CircleRadius
        for group in self.ballGroups:
            for _ in range(group.count):
                offset = Spacing.CircleRadius if pendingMove == self and group == self.ballGroups[0] else 0
                pygame.draw.circle(window, BallColors[group.color], [x,y-offset], Spacing.CircleRadius)
                if pendingMove != None and pendingMove.peek().color == group.color:
                    pygame.draw.circle(window, (0,0,0), [x,y-offset], Spacing.MatchCircleRadius)
                y += 2*Spacing.CircleRadius + Spacing.CircleVerticalSpacing

        hintColor = GameColors.KeyboardHintCanMoveTo if tubeCanBeNextMove else GameColors.KeyboardHintNormal
        hintImage = arialFont.render(keyboardHintCharacters[row][column], True, hintColor)
        hintImageRect = hintImage.get_rect()
        offset = Spacing.CircleRadius if pendingMove == self else 0
        window.blit(hintImage,
            (tubeCenter - hintImageRect.width/2, tubeTop - Spacing.CircleVerticalSpacing - hintImageRect.height - offset,
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

    def draw(self, pendingMove: Optional[Tube], screen: pygame.surface.Surface):
        rowWidth = GameData.TubesPerRow
        row = 0
        column = 0
        for tube in self.tubes:
            tube.draw(row, column, pendingMove)
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
            if t.canAddBallGroup(source.peek()):
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
        tubesLeft: int = Spacing.TubeMarginLeft - Spacing.TubeHorizontalSpacing//2
        tubesRight = Spacing.TubeMarginLeft + (GameData.TubesPerRow-1)*Spacing.CircleRadius*2 + GameData.TubesPerRow*Spacing.TubeHorizontalSpacing
        tubeHeight = GameData.BallsPerTube*Spacing.CircleRadius*2 + (GameData.BallsPerTube-1)*Spacing.CircleVerticalSpacing
        tubeTop = Spacing.tubeMarginTop - Spacing.TubeMarginAroundBalls
        if x < tubesLeft or x > tubesRight:
            return None
        column:int = (x - tubesLeft)//(Spacing.CircleRadius*2 + Spacing.TubeHorizontalSpacing)
        for row in range(4):
            rowTop = tubeTop+row*(tubeHeight+Spacing.TubeVerticalSpacing)
            rowBottom = rowTop + tubeHeight + 2*Spacing.TubeMarginAroundBalls
            if y >= rowTop and y <= rowBottom:
                return self.tubes[row*GameData.TubesPerRow+column]
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


window = pygame.display.set_mode((Spacing.ScreenWidth, Spacing.ScreenHeight))
pygame.display.set_caption("Ball Sort")
pygame.display.set_icon(pygame.image.load("icon.png"))
pygame.display.update()

tubeKeys = (
    pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
    pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r, pygame.K_t,
    pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g,
    pygame.K_z, pygame.K_x, pygame.K_c, pygame.K_v, pygame.K_b
)

tubes = TubeSet(GameData.FullTubes, GameData.EmptyTubes, GameData.BallsPerTube)
source: Optional[Tube] = None
closing = False
undoStack: list[MoveRecord] = []
redoStack: list[MoveRecord] = []
pendingMove: Optional[Tube] = None

def doMove(selectedTube: Tube):
    global pendingMove
    if pendingMove is selectedTube:
        pendingMove = None
    elif pendingMove is None and selectedTube is not None and not selectedTube.get_isEmpty():
        pendingMove = selectedTube
    elif pendingMove is not None and selectedTube is not None and selectedTube.canAddBallGroup(pendingMove.peek()):
        undoStack.append(MoveRecord(pendingMove, selectedTube))
        redoStack.clear()
        selectedTube.push(pendingMove.pop())
        pendingMove = None
    # todo else beep or something

# main loop
while not closing:
    # event handling, gets all event from the event queue
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            closing = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pendingMove = None
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            pendingMove = tubes.tryFindMove()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_LCTRL:
            if any(undoStack):
                moveToUndo = undoStack.pop()
                moveToUndo.source.push(BallGroup(color = moveToUndo.target.ballGroups[0].color, count = moveToUndo.count))
                moveToUndo.target.removeBalls(moveToUndo.count)
                redoStack.append(moveToUndo)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_y and event.mod & pygame.KMOD_LCTRL:
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
            
            #if selectedTube is not None:
            #    doMove(selectedTube)
    
    window.fill(black)
    tubes.draw(pendingMove, window)
    pygame.display.flip()

