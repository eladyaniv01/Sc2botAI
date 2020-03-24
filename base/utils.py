from scipy.spatial import Delaunay
import numpy as np


def get_edge_points(points: np.array, alpha: float, only_outer: bool = True) -> list:
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
            add_edge(edges, ia, ib)
            add_edge(edges, ib, ic)
            add_edge(edges, ic, ia)
    edge_points = []
    for i, j in edges:
        edge_points.append((points[[i, j], 0][1], points[[i, j], 1][0]))
    return edge_points


def extract_sub_matrix(matrix: np.array(), row_start_idx: int, row_end_idx: int, col_start_idx: int, col_end_idx: int) -> list:
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