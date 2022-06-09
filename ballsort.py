import time
from typing import Optional
import pygame
from BallGroup import BallGroup

from Drawing import Drawing
from GameColors import GameColors
from MoveRecord import MoveRecord
from Tube import Tube
from TubeSet import TubeSet
# import pygame_widgets.button

# To install requirements:
#  py -m pip uninstall pygame
#  py -m pip install pygame_widgets

# TODO:
# Refactor to not use globals
# Double-clicking a tube does a move
# Buttons:
#   Undo
#   Undo-to-checkpoint
#   ReDo
#   New Game
#   Game Size
# Better like-colors highlight
# Save State
# Allow transfers of partial stacks
# Detect Win and Loss

pygame.init()
pygame.font.init()

window = pygame.display.set_mode((Drawing.ScreenWidth, Drawing.ScreenHeight), pygame.RESIZABLE)
pygame.display.set_caption("Ball Sort")
pygame.display.set_icon(pygame.image.load("icon.png"))
pygame.display.update()

Drawing.resize(Drawing.ScreenWidth, Drawing.ScreenHeight)


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
        moving = pendingMove.pop()
        tubes.animateMove(window, pendingMove, selectedTube, moving, True)
        selectedTube.push(moving)
        pendingMove = None
    elif not selectedTube.get_isEmpty():
        setPendingMove(selectedTube)

def undo():
    if not undoStack:
        return
    moveToUndo = undoStack.pop()
    moving = BallGroup(color = moveToUndo.target.ballGroups[0].color, count = moveToUndo.count)
    moveToUndo.target.removeBalls(moveToUndo.count)
    tubes.animateMove(window, moveToUndo.target, moveToUndo.source, moving, False)
    moveToUndo.source.push(moving)
    redoStack.append(moveToUndo)

def redo():
    if not redoStack:
        return
    moveToRedo = redoStack.pop()
    moving = BallGroup(color = moveToRedo.source.ballGroups[0].color, count = moveToRedo.count)
    moveToRedo.source.removeBalls(moveToRedo.count)
    tubes.animateMove(window, moveToRedo.source, moveToRedo.target, moving, False)
    moveToRedo.target.push(moving)
    undoStack.append(moveToRedo)

while not closing:
    doRedraw = False
    # event handling, gets all event from the event queue
    for event in pygame.event.get():
        doRedraw = True
        if event.type == pygame.QUIT:
            closing = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
            pendingMove = None
            tubes = TubeSet(Drawing.FullTubes, Drawing.EmptyTubes, Drawing.BallsPerTube)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            setPendingMove(None)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            setPendingMove(tubes.tryFindMove(pendingMove))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL and event.mod & pygame.KMOD_SHIFT:
            setPendingMove(None)
            oldEmptyCount = tubes.numEmptyTubes()
            while any(undoStack) and tubes.numEmptyTubes() <= oldEmptyCount:
                undo()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL:
            setPendingMove(None)
            undo()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_y and event.mod & pygame.KMOD_CTRL:
            setPendingMove(None)
            redo()
        elif event.type == pygame.KEYDOWN and (tubes.isTubeKeyboardShortcut(event.key) or event.key == pygame.K_SPACE):
            if event.key == pygame.K_SPACE:
                selectedTube = None if pendingMove is None else tubes.tryGetAutoMove(pendingMove)
            else:
                selectedTube = tubes.getTubeForKeyStroke(event.key)

            if selectedTube is not None:
                doMove(selectedTube)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            (x,y) = event.pos
            selectedTube: Optional[Tube] = tubes.tryFindTubeByPosition((x,y))
            if selectedTube is not None:
                doMove(selectedTube)
        elif event.type == pygame.VIDEORESIZE:
            Drawing.resize(event.w, event.h)

    if doRedraw:
        window.fill(GameColors.WindowBackground)
        tubes.draw(window, None if pendingMove is None else pendingMove.peek())
    else:
        time.sleep(.01)
    pygame.display.flip()

