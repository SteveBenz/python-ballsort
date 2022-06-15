from BallGroup import BallGroup
from Tube import Tube

class MoveRecord:
    source: Tube
    target: Tube
    count: int

    def __init__(self, source: Tube, target: Tube, moving: BallGroup):
        self.count = moving.count
        self.source = source
        self.target = target
