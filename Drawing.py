
from math import ceil
from typing import Tuple
import pygame


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
    BallImagesHighlighted: list[pygame.Surface] = []

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

    HintFont: pygame.font.Font


    @staticmethod
    def resize(w: float, h: float) -> None:
        # TubeMarginLeft (1)
        # |  Circles (2)
        # |  |  TubeHorizontalSpacing (1.5)
        # 2 (for the margins)
        # (n-1) * 1.5  (for the spaces between)
        # 2*n for the tubes themselves
        # n*3 for the button column

        circleRadiusBasedOnWidth = w / (2*Drawing.TubesPerRow + 2 + (Drawing.TubesPerRow-1)*1.5 + 3)

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
        Drawing.BallImagesHighlighted.clear()
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
            ballImageHighlighted = pygame.Surface(ballImage.get_size(), pygame.SRCALPHA)
            ballImageHighlighted.blit(ballImage, (0,0))
            pygame.draw.circle(ballImageHighlighted, (0,0,0), (Drawing.CircleRadius, Drawing.CircleRadius), Drawing.CircleRadius*.2)
            Drawing.BallImagesHighlighted.append(ballImageHighlighted)
    
            Drawing.HintFont = pygame.font.SysFont('arial', 16)

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
    