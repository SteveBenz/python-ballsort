from typing import Final, Optional, Tuple, Union
import pygame
from BallGroup import BallGroup
from GameColors import GameColors
from pygame.surface import Surface
from pygame.rect import Rect
from pygame.font import Font, SysFont


class Tube:
    # Both of these are as-a-fraction-of-total-width
    __HORIZONTAL_SPACE_BETWEEN_TUBES: Final[float] = .15
    # This is horizontal and vertical, but it is a fraction of the total width of the rectangle.
    __SPACE_BETWEEN_BALLS: Final[float] = .1

    __cachedBallImages: list[Surface] = []
    __cachedBallImagesHighlighted: list[Surface] = []
    __cachedBallImagesRadius: float = -1

    __hintFont: Optional[Font] = None

    
    __ballColors = (
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

    def __init__(self, window: Surface, rect: Rect, hintKey: str, numBalls: int):
        if not Tube.__hintFont:
            Tube.__hintFont = SysFont('arial', 16)
        self.__emptySlots: int = numBalls
        self.__ballGroups: list[BallGroup] = list()
        self.rect: Rect = rect
        self.__window: Surface = window
        self.__numBalls: int = numBalls
        self.__hintKey = hintKey

    def peek(self) -> BallGroup:
        return self.__ballGroups[0]

    def serialize(self) -> list[int]:
        batch: list[int] = []
        for g in self.__ballGroups:
            for _ in range(g.count):
                batch.insert(0, g.color)
        return batch

    @property
    def emptySlots(self) -> int:
        return self.__emptySlots

    def pop(self, numBalls: int) -> BallGroup:
        assert self.__ballGroups[0].count >= numBalls
        if self.__ballGroups[0].count == numBalls:
            r = self.__ballGroups.pop(0)
        else:
            self.__ballGroups[0].count -= numBalls
            r = BallGroup(self.__ballGroups[0].color, numBalls)
        self.__emptySlots += numBalls
        return r

    def removeBalls(self, count: int) -> None:
        if self.__ballGroups[0].count == count:
            self.__ballGroups.pop(0)
        else:
            self.__ballGroups[0].count -= count
        self.__emptySlots += count

    def get_isEmpty(self) -> bool:
        return not any(self.__ballGroups)

    def get_isComplete(self) -> bool:
        return self.__emptySlots == self.__numBalls or (len(self.__ballGroups) == 1 and self.__emptySlots == 0)

    def canAddBallGroup(self, group: BallGroup) -> bool:
        if self.__emptySlots < group.count: return False
        if len(self.__ballGroups) == 0: return True
        return self.__ballGroups[0].color == group.color

    def canAddBallGroupPartial(self, group: BallGroup) -> bool:
        if self.__emptySlots == 0: return False
        if len(self.__ballGroups) == 0: return True
        return self.__ballGroups[0].color == group.color

    def push(self, group: BallGroup) -> None:
        if len(self.__ballGroups) > 0 and self.__ballGroups[0].color == group.color:
            self.__ballGroups[0].count += group.count
        else:
            self.__ballGroups.insert(0, group)
        self.__emptySlots -= group.count

    @staticmethod
    def getMaxUsableSize(size: Tuple[float,float], numBalls: int) -> Tuple[float,float]:
        """
        This widget requires a certain aspect-ratio in order to look right.
        The returned rectangle is the largest usable space within the given rectangle.
        """

        (width,height) = size
        # First let's look at what we get if width is the decider
        radius = width * (1 - Tube.__HORIZONTAL_SPACE_BETWEEN_TUBES - Tube.__SPACE_BETWEEN_BALLS) * .5
        spaceBetweenBalls = width * Tube.__SPACE_BETWEEN_BALLS
        # Padding at the top is 4x the radius
        heightIfWidthIsTheDecider = (radius*2+spaceBetweenBalls)*(numBalls+2)

        if heightIfWidthIsTheDecider <= height:
            return (width, heightIfWidthIsTheDecider)

        widthIfHeightIsTheDecider = width * height / heightIfWidthIsTheDecider
        return widthIfHeightIsTheDecider, height

    def getBallPosition(self, ballPosition: float) -> Rect:
        """
        Gets the rectangle where a ball should be drawn to given the current dimensions.  Note that ballPosition
        is a float, and at value 0, it means the top position for a ball in the tube and 1 is the second ball in
        the tube, and so on.  Values like .5 can be used to place a ball halfway in between the two slots and -1
        can be used to have a ball at the top of the tube.
        """
        spaceBetweenBalls = self.rect.width*Tube.__SPACE_BETWEEN_BALLS
        horizontalSpaceBetweenTubes = self.rect.width*Tube.__HORIZONTAL_SPACE_BETWEEN_TUBES
        radius = (self.rect.width - spaceBetweenBalls - horizontalSpaceBetweenTubes)/2
        left = self.rect.left + (spaceBetweenBalls + horizontalSpaceBetweenTubes)/2
        # Counting up from the bottom is less perilous
        top = self.rect.bottom + .5*spaceBetweenBalls - (self.__numBalls - ballPosition)*(radius*2+spaceBetweenBalls)
        return Rect(left,top,radius*2,radius*2)
    
    def getTubeRectangle(self) -> Rect:
        b0 = self.getBallPosition(0)
        spacing = self.rect.width*Tube.__SPACE_BETWEEN_BALLS
        return Rect(b0.left-spacing/2,b0.top-spacing/2,b0.width+spacing,(self.rect.bottom - b0.top)+spacing/2)

    def setPosition(self, newPosition: Rect) -> None:
        self.rect = newPosition

    def getBallImage(self, color: int, isHighlighted: bool) -> Surface:
        radius = self.getBallPosition(0).width/2
        if radius != Tube.__cachedBallImagesRadius:
            Tube.__cachedBallImages = []
            Tube.__cachedBallImagesHighlighted = []

        assert(len(Tube.__cachedBallImages) == len(Tube.__cachedBallImagesHighlighted))
        for i in range(len(Tube.__cachedBallImages), color+1):
            x = radius
            y = radius
            ballImage = Surface((2*radius,2*radius), pygame.SRCALPHA)
            if i % 5 == 0:
                pygame.draw.circle(ballImage, Tube.__ballColors[i], [x,y], radius)
            elif i % 5 == 1:
                pygame.draw.rect(ballImage, Tube.__ballColors[i], Rect(x-radius,y-radius,2*radius,2*radius))
            elif i % 5 == 2:
                pygame.draw.polygon(ballImage, Tube.__ballColors[i],
                    [(x,y-radius), 
                    (x-radius,y),
                    (x,y+radius),
                    (x+radius,y)])
            elif i % 5 == 3:
                pygame.draw.polygon(ballImage, Tube.__ballColors[i],
                    [(x,y-radius), 
                    (x-radius,y+radius),
                    (x+radius,y+radius)])
            elif i % 5 == 4:
                pygame.draw.polygon(ballImage, Tube.__ballColors[i],
                    [(x-radius,y-radius),
                    (x+radius,y-radius),
                    (x,y+radius)])
            Tube.__cachedBallImages.append(ballImage)
            ballImageHighlighted = Surface(ballImage.get_size(), pygame.SRCALPHA)
            ballImageHighlighted.blit(ballImage, (0,0))
            pygame.draw.circle(ballImageHighlighted, (0,0,0), (radius, radius), radius*.2)
            Tube.__cachedBallImagesHighlighted.append(ballImageHighlighted)

        if isHighlighted:
            return Tube.__cachedBallImagesHighlighted[color]
        else:
            return Tube.__cachedBallImages[color]

    def draw(self, canAddHighlight: bool, isSourceHighlight: bool, highlightedColor: Union[int,None]) -> None:
        backgroundColor = GameColors.ValidTargetTubeBackground if canAddHighlight else GameColors.TubeBackground
        hintColor = GameColors.KeyboardHintCanMoveTo if canAddHighlight else GameColors.KeyboardHintNormal
        pygame.draw.rect(self.__window, backgroundColor, self.getTubeRectangle())

        ballNumber = self.__emptySlots
        for group in self.__ballGroups:
            image = self.getBallImage(group.color, group.color == highlightedColor)
            for _ in range(group.count):
                self.__window.blit(image, self.getBallPosition(ballNumber - (.5 if isSourceHighlight and group is self.__ballGroups[0] else 0)))
                ballNumber += 1

        assert(Tube.__hintFont is not None)
        hintImage = Tube.__hintFont.render(self.__hintKey, True, hintColor)
        hintImageRect = hintImage.get_rect()
        hintPositionAsBall = self.getBallPosition(-1 - (.5 if isSourceHighlight else 0))
        hintLeft: float = hintPositionAsBall.left + (hintPositionAsBall.width - hintImageRect.width)/2
        self.__window.blit(hintImage, (hintLeft, hintPositionAsBall.top))
