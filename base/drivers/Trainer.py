from Sc2botAI.BaseBot import BaseBot, QLearningTable
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random, numpy as np

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units


KILL_UNIT_REWARD = 0.3
KILL_BUILDING_REWARD = 0.9
NO_MINERAL_FLOAT_REWARD = 0.5
NO_MINERAL_FLOAT_PENALTY = -0.5
GREATER_FOOD_REWARD = 0.4
GREATER_FOOD_PENALTY = -0.7
BREAK_ITERATION = 2000

class Trainer(BaseBot):
    def __init__(self, debug = False):
        super().__init__(debug=debug)
        self.sent_order = False
        # self.qlearn = QLearningTable(actions=list(range(len(smart_actions))))
        self.previous_killed_unit_score = 0
        self.previous_killed_building_score = 0
        self.previous_food_score = 0
        self.previous_minerals = 75
        self.previous_action = None
        self.previous_state = None
        self.action_space_cache = []



    async def on_step(self, iteration):
        await super().on_step(iteration)
        if self.iteration == BREAK_ITERATION:
            await self.client.leave()

        # training block

        enemy_units = self.enemy_units
        enemy_workers = self.enemy_units(UnitTypeId.DRONE)
        lings = self.enemy_units(UnitTypeId.ZERGLING)
        queens = self.enemy_units(UnitTypeId.QUEEN)
        lings = lings | queens
        good_units = enemy_workers | lings

        bad_units = [x for x in enemy_units if x not in good_units]
        bad_flying = [x for x in bad_units if (x.is_flying and x.type_id != UnitTypeId.OVERLORD)]
        for u in bad_flying:
            await self.client.debug_kill_unit(u)

        # if self.iteration % 500 == 0:
            # for u in bad_units:
            #     await self.client.debug_kill_unit(u)
        # if self.iteration == 2502:
        #     await self.client.leave()
        # if not self.units(UnitTypeId.THOR):
        #     await self.client.debug_create_unit(
        #         [[UnitTypeId.THOR, 1, self.main_base_ramp.depot_in_middle, 1]])

        if not self.units(UnitTypeId.REAPER):

            n = 1
            loc = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
            loc2 = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
            loc3 = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
            if self.iteration > 25:
                n = 1
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 1, loc2, 1]])
            if self.iteration > 325:
                n = 2
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 1, loc3, 1]])
            if self.iteration > 650:
                n = 3
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 1, loc2, 1]])
            if self.iteration > 900:
                n = 4
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 2, loc, 1]])


            return True

            if not self.enemy_units(UnitTypeId.QUEEN):
                await self.client.debug_create_unit(
                    [[UnitTypeId.QUEEN, 1, random.choice(self.enemy_start_locations), 2]])

        return True
        if not self.units(UnitTypeId.REAPER):
            for u in self.enemy_units:
                await self.client.debug_kill_unit(u)



            loc = self.game_info.map_center\
                .towards_with_random_angle(self.main_base_ramp.top_center,
                                           distance=30)
            loc2 = self.game_info.map_center\
                .towards_with_random_angle(self.enemy_start_locations[0],
                                           distance=30)
            await self.client.debug_create_unit(
                [[UnitTypeId.REAPER, 1, loc, 1], [UnitTypeId.ZERGLING, 3, loc, 2]])

            # await self.client.debug_create_unit(
            #     [[UnitTypeId.ZERGLING, 3, loc, 2]])

            return False

            if not self.enemy_units(UnitTypeId.QUEEN):
                await self.client.debug_create_unit(
                    [[UnitTypeId.QUEEN, 1, random.choice(self.enemy_start_locations), 2]])

        return True


def main():
    # map = random.choice(
    #     [
    #         'AbyssalReefLE',
    #         'AcropolisLE',
    #         'AutomatonLE',
    #         'BelShirVestigeLE',
    #         'CactusValleyLE',
    #         'CyberForestLE',
    #         'DiscoBloodbathLE',
    #         'EphemeronLE',
    #         'HonorgroundsLE',
    #         'KairosJunctionLE',
    #         'KingsCoveLE',
    #         'NewkirkPrecinctTE',
    #         'NewRepugnancyLE',
    #         'PaladinoTerminalLE',
    #         'PortAleksanderLE',
    #         'ProximaStationLE',
    #         'ThunderbirdLE',
    #         'TritonLE',
    #         'WintersGateLE',
    #         'WorldofSleepersLE',
    #         'YearZeroLE'
    #
    #     ]
    # )

    map = "AbyssalReefLE"
    sc2.run_game(
        sc2.maps.get(map),
        [Bot(Race.Terran, Trainer(debug = True)), Computer(Race.Zerg, Difficulty.Easy)],
        realtime=False,

        # sc2_version="4.10.1",
    )

if __name__ == "__main__":
    for i in range(20):
        print(f"i = {i}")
        main()