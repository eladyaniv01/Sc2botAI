from sc2.position import Point2
from sc2.game_info import Ramp
from typing import Optional, Union, List


# TODO  base manager here


class RampExt:
    def __init__(self, ramp=None, index=None, expansions=None):
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


class Expansion:

    def __init__(self, index=None, resources=None, coords=None, ramps=None, is_ours=False, is_enemies=False):
        """
        Basic object for storing expansion information
        """
        self.index = str(index)
        self.resources = resources
        self.coords: Point2 = coords
        self.ramps: Union[List[RampExt]] = ramps
        self.is_ours: bool = is_ours
        self.is_enemies: bool = is_enemies
        for ramp in self.ramps:
            ramp.name += f"+ of {self}"

    def __repr__(self):
        return f"<Expansion:[{self.index}]>"
