from sc2 import UnitTypeId
from sc2.position import Point2, Point3
from sc2.game_info import Ramp
from typing import Optional, Union, List
from scipy.spatial import Delaunay
import numpy as np
import math

# TODO  base manager here
def find_edges_with(i, edge_set):
    i_first = [j for (x,j) in edge_set if x==i]
    i_second = [j for (j,x) in edge_set if x==i]
    return i_first,i_second

def alpha_shape(points, alpha, only_outer=True):
    """
    Compute the alpha shape (concave hull) of a set of points.
    :param points: np.array of shape (n,2) points.
    :param alpha: alpha value.
    :param only_outer: boolean value to specify if we keep only the outer border
    or also inner edges.
    :return: set of (i,j) pairs representing edges of the alpha-shape. (i,j) are
    the indices in the points array.
    """
    assert points.shape[0] > 3, "Need at least four points"

    def add_edge(edges, i, j):
        """
        Add an edge between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in edges or (j, i) in edges:
            # already added
            assert (j, i) in edges, "Can't go twice over same directed edge right?"
            if only_outer:
                # if both neighboring triangles are in shape, it's not a boundary edge
                edges.remove((j, i))
            return
        edges.add((i, j))

    tri = Delaunay(points)
    edges = set()
    # Loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.vertices:
        pa = points[ia]
        pb = points[ib]
        pc = points[ic]
        # Computing radius of triangle circumcircle
        # www.mathalino.com/reviewer/derivation-of-formulas/derivation-of-formula-for-radius-of-circumcircle
        a = np.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
        b = np.sqrt((pb[0] - pc[0]) ** 2 + (pb[1] - pc[1]) ** 2)
        c = np.sqrt((pc[0] - pa[0]) ** 2 + (pc[1] - pa[1]) ** 2)
        s = (a + b + c) / 2.0
        area = np.sqrt(s * (s - a) * (s - b) * (s - c))
        circum_r = a * b * c / (4.0 * area)
        if circum_r < alpha:

            # ja = math.floor(math.sqrt(ia))
            # jb = math.floor(math.sqrt(ib))
            # jc = math.floor(math.sqrt(ic))
            add_edge(edges, ia, ib)
            add_edge(edges, ib, ic)
            add_edge(edges, ic, ia)
    return edges

def extract_sub_matrix(matrix, row_start_idx, row_end_idx, col_start_idx, col_end_idx):
    result = []
    print(f"row_start_idx : {row_start_idx}")
    print(f"row_end_idx : {row_end_idx}")
    print(f"col_start_idx : {col_start_idx}")
    print(f"col_end_idx : {col_end_idx}")
    for i in range(row_start_idx, row_end_idx):
        row = []
        for j in range(col_start_idx, col_end_idx):
            row.append(matrix[i][j])
        result.append(row)
    return result

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

    def __init__(self, ai=None, index=None, resources=None, coords=None, ramps=None, is_ours=False, is_enemies=False):
        """
        Basic object for storing expansion information
        """
        self.ai = ai
        self.grid = self.ai.game_info.placement_grid.data_numpy
        self.index = str(index)
        self.resources = resources
        self.coords: Point2 = coords
        self.grid_points = [[]]
        x_offset = Point2((20.0,0.0))
        y_offset = Point2((0.0,20.0))
        # need to assert the points are in the map actually
        self.top_left = Point2(self.coords.offset((-x_offset)).offset(y_offset))
        self.bottom_right = Point2(self.coords.offset((x_offset)).offset(-y_offset))
        self.ramps: Union[List[RampExt]] = ramps
        self.is_ours: bool = is_ours
        self.is_enemies: bool = is_enemies

        self.borders = []
        for ramp in self.ramps:
            ramp.name += f"+ of {self}"



    def in_placement_grid(self, p):
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


    def same_height(self, p0, p1):
        h0 = self.ai.get_terrain_z_height(p0)
        h1 = self.ai.get_terrain_z_height(p1)
        return h0 == h1

    def set_borders(self):
        self.coords = self.coords.rounded
        loc = self.coords
        r = 18
        row_start = loc.y - r
        row_end = loc.y + r
        col_start = loc.x - r
        col_end = loc.x + r
        points = []
        p_arr = []
        for (b, a), value in np.ndenumerate(self.grid):
            p = (a, b)
            # skip non placements which are zero
            if value == 0 or not self.same_height(Point2(p),self.coords):
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
        edges = alpha_shape(p_arr,0.8)
        edge_points = []
        for i, j in edges:
            edge_points.append((p_arr[[i, j], 0][1],p_arr[[i, j], 1][0]))
        self.borders = edge_points




    def is_in(self, coords: Union[Point2, Point3]) -> bool:
        if self.top_left.x <= coords.x <= self.bottom_right.x and self.top_left.y >= coords.y >= self.bottom_right.y:
            return True
        return False

    def __repr__(self):
        return f"<Expansion:[{self.index}]>"
