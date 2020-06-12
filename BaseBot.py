import os
import sys
import logging
import math
from math import atan2, degrees
from sc2.unit import Unit

from settings import PROJECT_DIR

sys.path.append(os.path.join(os.path.dirname(__file__), PROJECT_DIR))
import numpy as np
import sc2
from sc2.position import Point2, Point3
from base.managers.map_manager import MapManager
from base.managers.debug_manager import DebugManager
from datetime import datetime as dt
from base.drivers.reaper import ReaperDriver
# from base.drivers.reaper_q import ReaperQAgent
# from settings import QFILE
from base.drivers.BaseDriver import UnitPriority
from UnitRole import UnitRole



class BaseBot(sc2.BotAI):
    def __init__(self, debug=False):
        super().__init__()
        self.created_at = dt.timestamp(dt.now())
        self.debug = debug
        self.debug_manager = DebugManager(ai=self)
        self.map_manager = MapManager(ai=self)
        self._solved = False
        self.drivers = [ReaperDriver(ai=self)]
        self.iteration = 0
        self.roles = {role: [] for role in UnitRole}
        self.logger = logging.getLogger()

    def log_it(self, message: str, log_level=logging.INFO):
        message = f"[TAG] {message}"
        self.logger.log(log_level,message)



    async def on_step(self, iteration):
        self.iteration = iteration
        self.client.game_step = 4
        if not self._solved:
            self.map_manager.solve_expansions()
            self._solved = True
        for driver in self.drivers:
            if self.units(driver.condition):
                await driver.execute()
        # debug always last
        if self.debug:
            self.debug_manager.draw_debug()

            async def on_building_construction_started(self, unit: Unit):
                self.log_it(f"Construction of building {unit} started at {unit.position}.")

            async def on_building_construction_complete(self, unit: Unit):
                self.log_it(f"Construction of building {unit} completed at {unit.position}.")

            async def on_enemy_unit_entered_vision(self, unit: Unit):
                self.log_it(f" {unit} entered vision at {unit.position}.")

    async def on_unit_created(self, unit: Unit):
        self.roles[UnitRole.New].append(unit.tag)
        # self.log_it(f" {unit} added to  self.roles[UnitRole.New].")

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
        return atan2(
            change_in_y, change_in_x
        )  # add degrees() around  if you want your answer in degrees

    def distance_math_hypot(self, p0, p1):
        p0, p1 = self._convert_to_tuple(p0), self._convert_to_tuple(p1)
        return math.hypot(p0[0] - p1[0], p0[1] - p1[1])

    def calculate_angle_distance(self, p0, p1):
        return self.solve_angle(p0, p1), self.distance_math_hypot(p0, p1)

    def __repr__(self):
        return f"<BaseBot: {str(self.created_at)}>"
