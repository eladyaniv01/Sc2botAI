from Sc2botAI.BaseBot import BaseBot
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
import logging
import random
from sc2.constants import *
from sc2 import Race, Difficulty, maps
from sc2.player import Bot, Computer, Human
from base.drivers import Trainer
from importlib import reload
import sc2
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )
BREAK_ITERATION = 605 # before zerg makes mutas


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
        return True
        if self.iteration == BREAK_ITERATION:
            await self.client.leave()

        # training block - managing the  'env'

        enemy_units = self.enemy_units
        enemy_workers = self.enemy_units(UnitTypeId.DRONE)
        lings = self.enemy_units(UnitTypeId.ZERGLING)
        queens = self.enemy_units(UnitTypeId.QUEEN)
        lings = lings | queens
        good_units = enemy_workers | lings

        bad_units = [x for x in enemy_units if x not in good_units]
        bad_flying = [x for x in bad_units if (x.is_flying and x.type_id != UnitTypeId.OVERLORD)]
        for u in bad_flying:
            await self.client.debug_kill_unit(u) #shouldnt happen ->  kill mutas

        if not self.units(UnitTypeId.REAPER):
            loc = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
            loc2 = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=5)
            loc3 = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
            if self.iteration > 0:
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 1, loc2, 1]])
            if self.iteration > 325:
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 1, loc3, 1]])
            if self.iteration > 650:
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 1, loc2, 1]])
            if self.iteration > 900:
                await self.client.debug_create_unit(
                    [[UnitTypeId.REAPER, 2, loc, 1]])

        killed_value_units = self.state.score.killed_value_units
        lost_reapers = self.state.score.lost_minerals_army + self.state.score.lost_vespene_army
        if lost_reapers == 0:
            lost_reapers = 1
        print(
            f"\riteration : {self.iteration}, Score : {(killed_value_units / lost_reapers):.2f}",
            end="")


# def main():
#     map = "AbyssalReefLE"
#     sc2.run_game(
#         sc2.maps.get(map),
#         [Bot(Race.Terran, Trainer(debug = False)), Computer(Race.Zerg, Difficulty.Easy)],
#         realtime=False,
#
#         # sc2_version="4.10.1",
#     )
# if __name__ == "__main__":
#     for i in range(20):
#         main()



#
def main():
    player_config = [Bot(Race.Terran, Trainer(debug=True)), Computer(Race.Zerg, Difficulty.Easy)]
    map = "Abyssal Reef LE"
    map = "ReaperTraining1"
    gen = sc2.main._host_game_iter(maps.get(map), player_config, realtime=False)

    for i in range(200):
        print(f"i = {i}")
        r = next(gen)

        # reload(Trainer)
        player_config[0].ai = Trainer(debug=True)
        gen.send(player_config)


if __name__ == "__main__":
    main()