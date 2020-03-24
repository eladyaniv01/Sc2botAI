from sc2 import bot_ai
from sc2.ids.unit_typeid import UnitTypeId
from Sc2botAI.base.drivers.reaper_q import ReaperQAgent
drivers = {
    UnitTypeId.REAPER: ReaperQAgent
}


class DriverManager:
    def __init__(self, ai: Union[bot_ai, None] = None):
        self.ai = ai

    def set_drivers(self):
        units = self.ai.units
