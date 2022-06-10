from typing import Optional
import pygame
from BallGroup import BallGroup
from Drawing import Drawing
from GameColors import GameColors


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

    def draw(self, window: pygame.surface.Surface, row: int, column: int, pendingMove: Optional[BallGroup], hintKey: str) -> None:
        tubeCanBeNextMove = pendingMove != None and self.canAddBallGroup(pendingMove)
        background = GameColors.ValidTargetTubeBackground if tubeCanBeNextMove else GameColors.TubeBackground
        pygame.draw.rect(window, background, Drawing.getTubeRect(column, row))

        ballNumber = self.emptySlots
        for group in self.ballGroups:
            for _ in range(group.count):
                image = Drawing.BallImagesHighlighted[group.color] if pendingMove is not None and pendingMove.color == group.color \
                    else Drawing.BallImages[group.color]
                center = Drawing.getCircleCenter(ballNumber, column, row, group is pendingMove)
                ballNumber += 1
                window.blit(image, (center[0] - Drawing.CircleRadius, center[1] - Drawing.CircleRadius))

        hintColor = GameColors.KeyboardHintCanMoveTo if tubeCanBeNextMove else GameColors.KeyboardHintNormal
        hintImage = Drawing.HintFont.render(hintKey, True, hintColor)
        hintImageRect = hintImage.get_rect()
        topCircleCenter = Drawing.getCircleCenter(0, column, row, (not self.get_isEmpty()) and pendingMove == self.peek())
        window.blit(hintImage,
            (topCircleCenter[0] - hintImageRect.width/2, topCircleCenter[1] - Drawing.CircleVerticalSpacing - Drawing.CircleRadius - hintImageRect.height,
            hintImageRect.width, hintImageRect.height))
