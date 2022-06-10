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

class BallSortGame:
    window = pygame.display.set_mode((Drawing.ScreenWidth, Drawing.ScreenHeight), pygame.RESIZABLE)
    tubes = TubeSet(Drawing.FullTubes, Drawing.EmptyTubes, Drawing.BallsPerTube)
    source: Optional[Tube] = None
    undoStack: list[MoveRecord] = []
    redoStack: list[MoveRecord] = []
    pendingMove: Optional[Tube] = None

    def setPendingMove(self, selectedTube: Optional[Tube]) -> None:
        if selectedTube is not self.pendingMove:
            self.tubes.animateSelection(self.window, selectedTube, self.pendingMove)
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
            self.tubes.animateMove(self.window, self.pendingMove, selectedTube, moving, True)
            selectedTube.push(moving)
            self.pendingMove = None
        elif not selectedTube.get_isEmpty():
            self.setPendingMove(selectedTube)

    def undo(self):
        if not self.undoStack:
            return
        moveToUndo = self.undoStack.pop()
        moving = BallGroup(color = moveToUndo.target.ballGroups[0].color, count = moveToUndo.count)
        moveToUndo.target.removeBalls(moveToUndo.count)
        self.tubes.animateMove(self.window, moveToUndo.target, moveToUndo.source, moving, False)
        moveToUndo.source.push(moving)
        self.redoStack.append(moveToUndo)

    def redo(self):
        if not self.redoStack:
            return
        moveToRedo = self.redoStack.pop()
        moving = BallGroup(color = moveToRedo.source.ballGroups[0].color, count = moveToRedo.count)
        moveToRedo.source.removeBalls(moveToRedo.count)
        self.tubes.animateMove(self.window, moveToRedo.source, moveToRedo.target, moving, False)
        moveToRedo.target.push(moving)
        self.undoStack.append(moveToRedo)

    def main(self) -> None:
        pygame.init()
        pygame.font.init()

        pygame.display.set_caption("Ball Sort")
        pygame.display.set_icon(pygame.image.load("icon.png"))
        pygame.display.update()

        Drawing.resize(Drawing.ScreenWidth, Drawing.ScreenHeight)

        closing = False
        while not closing:
            doRedraw = False
            # event handling, gets all event from the event queue
            for event in pygame.event.get():
                doRedraw = True
                if event.type == pygame.QUIT:
                    closing = True
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                    self.pendingMove = None
                    self.tubes = TubeSet(Drawing.FullTubes, Drawing.EmptyTubes, Drawing.BallsPerTube)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.setPendingMove(None)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    self.setPendingMove(self.tubes.tryFindMove(self.pendingMove))
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL and event.mod & pygame.KMOD_SHIFT:
                    self.setPendingMove(None)
                    oldEmptyCount = self.tubes.numEmptyTubes()
                    while any(self.undoStack) and self.tubes.numEmptyTubes() <= oldEmptyCount:
                        self.undo()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_z and event.mod & pygame.KMOD_CTRL:
                    self.setPendingMove(None)
                    self.undo()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_y and event.mod & pygame.KMOD_CTRL:
                    self.setPendingMove(None)
                    self.redo()
                elif event.type == pygame.KEYDOWN and (self.tubes.isTubeKeyboardShortcut(event.key) or event.key == pygame.K_SPACE):
                    if event.key == pygame.K_SPACE:
                        selectedTube = None if self.pendingMove is None else self.tubes.tryGetAutoMove(self.pendingMove)
                    else:
                        selectedTube = self.tubes.getTubeForKeyStroke(event.key)

                    if selectedTube is not None:
                        self.doMove(selectedTube)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    (x,y) = event.pos
                    selectedTube: Optional[Tube] = self.tubes.tryFindTubeByPosition((x,y))
                    if selectedTube is not None:
                        self.doMove(selectedTube)
                elif event.type == pygame.VIDEORESIZE:
                    Drawing.resize(event.w, event.h)

            if doRedraw:
                self.window.fill(GameColors.WindowBackground)
                self.tubes.draw(self.window, None if self.pendingMove is None else self.pendingMove.peek())
            else:
                time.sleep(.01)
            pygame.display.flip()

BallSortGame().main()
