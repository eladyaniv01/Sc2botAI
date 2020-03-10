from Sc2botAI.base.BuildArea import BuildArea
from Sc2botAI.base.Cliff import Cliff


class GridArea:
    def __init__(self, area: BuildArea):
        self.Area: BuildArea = area
        self.BuildingIndex = -1
        self.Cliff = Cliff.No
