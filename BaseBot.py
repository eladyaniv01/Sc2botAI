import os
import sys

import math
from math import atan2,degrees
from sc2.unit import Unit

from Sc2botAI.settings import PROJECT_DIR

sys.path.append(os.path.join(os.path.dirname(__file__), PROJECT_DIR))
import numpy as np
import sc2
from sc2.position import Point2, Point3
from Sc2botAI.base.managers.map_manager import MapManager
from Sc2botAI.base.managers.debug_manager import DebugManager
from datetime import datetime as dt
from Sc2botAI.base.drivers.reaper import ReaperDriver
from Sc2botAI.base.drivers.reaper_q import ReaperQAgent

qfile = "reaper_q_driver.pickle"

class BaseBot(sc2.BotAI):

    def __init__(self, debug=False):
        super().__init__()
        ra = ReaperQAgent(ai=self)
        import pickle
        if os.path.exists(qfile):
            with open(qfile, "rb") as f:
                ra = ReaperQAgent(ai=self, qtable=pickle.load(f))
        self.created_at = dt.timestamp(dt.now())
        self.debug = debug
        self.debug_manager = DebugManager(ai=self)
        self.map_manager = MapManager(ai=self)
        self._solved = False
        # self.drivers = [ReaperDriver(ai=self)]
        self.drivers = [ra]
        self.iteration = 0

    async def on_step(self, iteration):
        self.iteration = iteration
        if not self._solved:
            # self.map_manager.solve_expansions()
            self._solved = True
        for driver in self.drivers:
            if self.units(driver.condition):
                await driver.execute()
        # debug always last
        if self.debug:
            self.debug_manager.draw_debug()

            async def on_building_construction_started(self, unit: Unit):
                print(f"Construction of building {unit} started at {unit.position}.")

            async def on_building_construction_complete(self, unit: Unit):
                print(f"Construction of building {unit} completed at {unit.position}.")

            async def on_enemy_unit_entered_vision(self, unit: Unit):
                print(f" {unit} entered vision at {unit.position}.")

    def _convert_to_tuple(self, p0):
        if isinstance(p0, Point2):
            return p0.x, p0.y
        if isinstance(p0, Point3):
            return p0.x, p0.y
        return p0

    def solve_angle(self, p0, p1):
        p0, p1 = self._convert_to_tuple(p0), self._convert_to_tuple(p1)
        change_in_x = p1[0] - p0[0]
        change_in_y = p1[1] - p0[1]
        return atan2(change_in_y, change_in_x) #add degrees() around  if you want your answer in degrees

    def distance_math_hypot(self, p0, p1):
        p0, p1 = self._convert_to_tuple(p0), self._convert_to_tuple(p1)
        return math.hypot(p0[0] - p1[0], p0[1] - p1[1])

    def calculate_angle_distance(self, p0, p1):
        return self.solve_angle(p0, p1), self.distance_math_hypot(p0, p1)

    def __repr__(self):
        return f'<BaseBot: {str(self.created_at)}>'
