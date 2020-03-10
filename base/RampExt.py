from sc2.game_info import Ramp
from sc2.position import Point2


class RampExt:
    def __init__(self, ramp: Ramp = None, index: int = None, expansions: list= None):
        """
        Basic object for storing Ramp information
        """
        if expansions:
            self.expansions = expansions
        else:
            self.expansions = []
        self.raw_ramp = ramp
        self.index = index
        self.name = "Ramp"
        self.coords: Point2 = ramp.top_center

    def __repr__(self):
        return f"<Ramp[{self.index}]>"