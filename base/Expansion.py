from sc2.position import Point2
from sc2.game_info import Ramp


class Expansion:
    def __init__(self,name="Expansion",resources = None,  coords=None,ramp=None, is_ours=False, is_enemies=False):
        """
        Basic object for storing expansion information
        """
        self.name = name
        self.resources = resources
        self.coords: Point2 = coords
        self.ramp: Ramp = ramp
        self.is_ours: bool = is_ours
        self.is_enemies: bool = is_enemies





