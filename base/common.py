from sc2 import UnitTypeId
from sc2.position import Point2, Point3
from sc2.game_info import Ramp
from typing import Optional, Union, List

import numpy as np

from .utils import get_edge_points



# TODO  base manager here




class Rectangle:
    def __init__(self, x: int, y:int, width: int, height: int):
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(width, int)
        assert isinstance(height, int)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height






