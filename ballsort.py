from array import array
from asyncio import constants
from cmath import rect
from operator import truediv
import random
import sys
from turtle import circle, screensize
import pygame

# Gotta do this first:
#  py -m pip install pygame
#
# If errors, maybe do this first:
#  py -m pip uninstall pygame

pygame.init()

white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
brown = (255, 255, 0)
purple = (255, 0, 255)
black = (0, 0, 0)

BallColors = (
    (255, 255, 255),
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (96, 0, 0), (0, 128, 0), (0, 0, 128),
    (96, 96, 0), (96, 0, 96), (0, 96, 96),
    (255, 96, 96), (96, 255, 96), (96, 96, 255),
    (255, 255, 96), (255, 96, 255), (96, 255, 255)
)

class GameColors:
    TubeBackground = (50,50,50)
    WindowBackground = (0,0,0)

class Spacing:
    CircleRadius = 10
    MatchCircleRadius = 2
    tubeMarginTop = 50
    TubeMarginLeft = CircleRadius
    CircleVerticalSpacing = CircleRadius/5
    TubeHorizontalSpacing = CircleRadius*1.5
    TubeVerticalSpacing = CircleRadius*3
    TubeMarginAroundBalls = 3

    ScreenWidth = 650
    ScreenHeight = 700

class GameData:
    BallsPerTube = 6
    FullTubes = 16
    EmptyTubes = 3

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

    def get_isEmpty(self) -> bool:
        return self.ballGroups.count == 0

    def get_isComplete(self) -> bool:
        return self.ballGroups.count == 1 and self.emptySlots == 0

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

    def draw(self, row: int, column: int, pendingMove: 'Tube') -> None:
        tubeCenter = Spacing.TubeMarginLeft + column*(Spacing.CircleRadius*2 + Spacing.TubeHorizontalSpacing) + Spacing.CircleRadius
        tubeTotalHeight = GameData.BallsPerTube*Spacing.CircleRadius*2 + (GameData.BallsPerTube-1)*Spacing.CircleVerticalSpacing
        tubeTop = Spacing.tubeMarginTop + row*(tubeTotalHeight + Spacing.TubeVerticalSpacing)
        pygame.draw.rect(window, GameColors.TubeBackground,
            (tubeCenter - Spacing.CircleRadius - Spacing.TubeMarginAroundBalls,
            tubeTop - Spacing.TubeMarginAroundBalls,
            (Spacing.CircleRadius + Spacing.TubeMarginAroundBalls)*2,
            tubeTotalHeight + 2*Spacing.TubeMarginAroundBalls))

        x = tubeCenter
        y = tubeTop + self.emptySlots*(2*Spacing.CircleRadius + Spacing.CircleVerticalSpacing) + Spacing.CircleRadius
        for group in self.ballGroups:
            for i in range(group.count):
                offset = Spacing.CircleRadius if pendingMove == self and group == self.ballGroups[0] else 0
                pygame.draw.circle(window, BallColors[group.color], [x,y-offset], Spacing.CircleRadius)
                if pendingMove != None and pendingMove.peek().color == group.color:
                    pygame.draw.circle(window, (0,0,0), [x,y-offset], Spacing.MatchCircleRadius)
                y += 2*Spacing.CircleRadius + Spacing.CircleVerticalSpacing

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

    def move(self, frm: Tube, to: Tube):
        to.push(frm.frm.pop())
    
    def draw(self, pendingMove: Tube, screen: pygame.Surface):
        rowWidth = 5
        row = 0
        column = 0
        for tube in self.tubes:
            tube.draw(row, column, pendingMove)
            column += 1
            if column == rowWidth:
                column = 0
                row += 1


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
source: Tube or None = None
closing = False
# main loop
pendingMove = None
while not closing:
    # event handling, gets all event from the event queue
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            closing = True
        elif event.type == pygame.KEYDOWN and event.key in tubeKeys:
            moveIndex = tubeKeys.index(event.key)
            if moveIndex != None:
                selectedTube = tubes.tubes[moveIndex]
                if pendingMove == None:
                    if not selectedTube.get_isEmpty():
                        pendingMove = selectedTube
                    # todo else beep or something
                else:
                    if pendingMove == selectedTube:
                        pendingMove = None
                    elif selectedTube.canAddBallGroup(pendingMove.peek()):
                        selectedTube.push(pendingMove.pop())
                        pendingMove = None
                    # todo else beep or something
    
    window.fill(black)
    tubes.draw(pendingMove, window)
    pygame.display.flip()

