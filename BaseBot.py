import os
import sys
from Sc2botAI.settings import PROJECT_DIR

sys.path.append(os.path.join(os.path.dirname(__file__), PROJECT_DIR))
import numpy as np
import sc2
from sc2.position import Point2, Point3
from Sc2botAI.base.managers.map_manager import MapManager
from Sc2botAI.base.managers.debug_manager import DebugManager
from datetime import datetime as dt


class BaseBot(sc2.BotAI):

    def __init__(self, debug=False):
        super().__init__()
        self.created_at = dt.timestamp(dt.now())
        self.debug = debug
        if self.debug:
            self.debug_manager = DebugManager(ai=self)
        self.map_manager = MapManager(ai=self)

    async def on_step(self, iteration):
        self.map_manager.solve_expansions()

        # debug always last
        if self.debug:
            self.debug_manager.draw_debug()

    def __repr__(self):
        return f'<BaseBot: {str(self.created_at)}>'
