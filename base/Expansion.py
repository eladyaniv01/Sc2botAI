from typing import List, Union

import numpy as np

from sc2.position import Point2, Point3
from .RampExt import RampExt
from Sc2botAI.base.utils import get_edge_points


class Expansion:

    def __init__(self, ai=None, index=None, resources=None, coords=None, ramps=None, is_ours=False, is_enemies=False):
        """
        Basic object for storing expansion information
        """
        self.ai = ai
        self.grid = self.ai.game_info.placement_grid.data_numpy
        self.index = str(index)
        self.resources = resources
        self.coords: Point2 = coords
        self.turret_positions = [[]]
        self.turret_queue = None
        self.grid_points = [[]]
        x_offset = Point2((20.0,0.0))
        y_offset = Point2((0.0,20.0))
        # need to assert the points are in the map actually
        self.top_left = Point2(self.coords.offset(-x_offset).offset(y_offset))
        self.bottom_right = Point2(self.coords.offset(x_offset).offset(-y_offset))
        self.ramps: Union[List[RampExt]] = ramps
        self.is_ours: bool = is_ours
        self.is_enemies: bool = is_enemies

        self.borders = []
        for ramp in self.ramps:
            ramp.name += f"+ of {self}"

    def in_placement_grid(self, p: Union[Point2,Point3]) -> bool:
        x,y = int(p.x),int(p.y)
        height = len(self.grid)
        width = len(self.grid[0])
        try:
            (y < height and x < width and self.grid[x][y])
        except Exception as e:
            print(e)
            print(f"x : {x} , type : {type(x)}")
            print(f"y : {y} , type : {type(y)}")
            print(f"p : {p} , type : {type(p)}")
        return y < height and x < width and self.grid[x][y]

    def same_height(self, p0: Point2, p1: Point2) -> bool:
        h0 = self.ai.get_terrain_z_height(p0)
        h1 = self.ai.get_terrain_z_height(p1)
        return h0 == h1

    def solve_turret_placements(self):
        edge_points = sorted(self.borders)
        self.turrets = edge_points[0:-1:9]
        self.turret_queue = set(self.turrets)

    def fix_borders(self):
        expos_rounded = [p.rounded for p in list(self.ai.expansion_locations.keys())]

        li = []
        for border in self.borders:
            b = Point2(border)
            for exp in expos_rounded:
                if self.same_height(exp,b):
                    if exp != self.coords:
                        if 15 > exp.distance_to(b) > 5:
                            li.append(border)
                    else:
                        li.append(border)
        self.borders = list(set(li))

    def set_borders(self, r=18):
        self.coords = self.coords.rounded
        step = 1
        height_here = self.ai.game_info.terrain_height[self.coords]
        main_height = self.ai.game_info.terrain_height[self.ai.start_location.rounded]
        natural_height = self.ai.game_info.terrain_height[self.ai.main_base_ramp.lower.pop()]# doesnt matter which
        # if height_here == main_height:
        #     r = 20
        # elif height_here == natural_height:
        #     print(natural_height)
        #     r = 15
        #     step = 2
        # else:
        #     self.borders = []
        #     return True
        loc = self.coords

        row_start = loc.y - r
        row_end = loc.y + r
        col_start = loc.x - r
        col_end = loc.x + r
        points = []
        p_arr = []
        for (b, a), value in np.ndenumerate(self.grid):
            p = (a, b)
            # skip non placements which are zero
            if value == 0 or not self.same_height(Point2(p), self.coords):
                continue
            # skip if not in expansion zone
            if not (col_start <= a <= col_end):
                continue
            if not (row_start <= b <= row_end):
                continue
            points.append(p)
            point = []
            point.append(p[0])
            point.append(p[1])
            p_arr.append(point)
        self.grid_points = points
        p_arr = np.array(p_arr)
        edges = get_edge_points(p_arr, 0.8)
        # final_edges = []
        # step = 1
        # for i in range(0,len(edges),step):
        #     final_edges.append(edges[i])
        # self.borders = final_edges
        self.borders = edges
        self.fix_borders()
        self.solve_turret_placements()

    def __repr__(self):
        return f"<Expansion:[{self.index}]>"