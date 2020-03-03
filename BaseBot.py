
import os
import sys
from Sc2botAI.settings import PROJECT_DIR
sys.path.append(os.path.join(os.path.dirname(__file__), PROJECT_DIR))
from sc2 import run_game, maps

import numpy as np

import sc2
from sc2 import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.position import Point2, Point3
from sc2.game_info import Ramp
from Sc2botAI import base
from Sc2botAI.base.managers.expansion_manager import ExpansionManager


class BaseBot(sc2.BotAI):

    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self._cached_ramps = {}
        self.expansion_manager = ExpansionManager(ai = self)


    async def on_step(self, iteration):
        self.expansion_manager.solve_expansions()

        if self.debug:
            self.draw_debug()

    def draw_debug(self):
        # self.draw_placement_grid()
        self.draw_ramps()
        self.draw_expansions()
        for structure in self.structures:
            self._client.debug_text_world(
                "\n".join(
                    [
                        f"{structure.type_id.name}:{structure.type_id.value}",
                        f"({structure.position.x:.2f},{structure.position.y:.2f})",
                        f"{structure.build_progress:.2f}",
                    ]
                    + [repr(x) for x in structure.orders]
                ),
                structure.position3d,
                color=(0, 255, 0),
                size=12,
            )

    def draw_placement_grid(self):
        map_area = self._game_info.playable_area
        for (b, a), value in np.ndenumerate(self._game_info.placement_grid.data_numpy):
            if value == 0:
                continue
            # Skip values outside of playable map area
            if not (map_area.x <= a < map_area.x + map_area.width):
                continue
            if not (map_area.y <= b < map_area.y + map_area.height):
                continue
            p = Point2((a, b))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # print(f"Drawing {p0} to {p1}")
            color = Point3((0, 255, 0))
            self._client.debug_box_out(p0, p1, color=color)

    def draw_ramps(self):
        map_area = self._game_info.playable_area
        nat = None

        for index, ramp in enumerate(self._game_info.map_ramps):
            self._cached_ramps[index] = ramp

            if ramp == self.main_base_ramp:
                name = "MAIN RAMP"
            else:
                name = "RAMP"
            p = ramp.depot_in_middle

            # print(f"{index} : {p}")
            if p is not None:

                # print(p)
                h2 = self.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 1.5, pos.y - 1.5, pos.z + 1.5)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + 1.5, pos.y + 1.5, pos.z - 1.5)) + Point2((0.5, 0.5))
                # print(f"Drawing {p0} to {p1}")
                color = Point3((0, 255, 0))
                self._client.debug_box_out(p0, p1, color=color)
                self._client.debug_text_world(
                    "\n".join(
                        [
                            f"{name} {index}",
                            f"Coords: ({p.position.x:.2f},{p.position.y:.2f})",

                        ]
                    ),
                    pos,
                    color=(0, 255, 0),
                    size=12,
                )

    def draw_expansions(self):

        expansion_dict = self.expansion_manager.expansions
        for index, info in expansion_dict.items():
            location, resources = info.coords, info.resources
            name = "Expansion"
            if index == 1:
                name = "Expansion - Natural"
            elif index == 2 or index == 3:
                name = "Expansion - optional third"
            p = location

            if isinstance(p, Point2):

                h2 = self.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 2, pos.y - 2, pos.z + 2)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + 2, pos.y + 2, pos.z - 2)) + Point2((0.5, 0.5))
                distance_to_main = p.distance_to_point2(self.main_base_ramp.depot_in_middle)
                if distance_to_main < 16.0:
                    continue

                color = Point3((0, 255, 0))
                self._client.debug_box_out(p0, p1, color=color)
                self._client.debug_text_world(
                    "\n".join(
                        [
                            f"{name} {index}",
                            f"distance_to_main: {distance_to_main:.2f}",
                            f"Coords: ({p.position.x:.2f},{p.position.y:.2f})",
                            f"Resources: ({len(resources)})",
                        ]
                    ),
                    pos,
                    color=(0, 255, 0),
                    size=12,
                )

run_game(
    maps.get("AutomatonLE"),
    [Bot(Race.Terran, BaseBot(debug=True)), Computer(Race.Protoss, Difficulty.Easy)],
    realtime=True,
)


