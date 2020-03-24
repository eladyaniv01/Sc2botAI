from sc2 import run_game, Race, Difficulty, maps, UnitTypeId
from sc2.player import Bot, Computer, Human
from Sc2botAI.BaseBot import BaseBot
import random


class DummyBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.was_done = False

    async def on_step(self, iteration):
        await super().on_step(iteration)

        if not self.units(UnitTypeId.REAPER):
            loc = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
            await self.client.debug_create_unit(
                [[UnitTypeId.REAPER, 1, loc, 1]])

        print(self.state.score.score)

        for unit in self.enemy_units:
            await self.client.debug_kill_unit(unit)

        print(self.state.score.score)

        await self.client.leave()
run_game(
    maps.get("AbyssalReefLE"),
    # [Bot(Race.Terran, BaseBot(debug=True)), Computer(Race.Terran, Difficulty.VeryHard)],
    [Bot(Race.Terran,DummyBot()), Computer(Race.Terran, Difficulty.VeryHard)],
    realtime=True,
)
