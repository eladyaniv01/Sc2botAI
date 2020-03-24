from typing import List, Union, Tuple
from sc2 import bot_ai

from sc2.position import Point3, Point2
import numpy as np

from Sc2botAI.base.Expansion import Expansion

GREEN = Point3((0, 255, 0))
RED = Point3((255, 0, 0))
BLUE = Point3((0, 0, 255))


class DebugManager:
    def __init__(self, ai: Union[bot_ai, None] = None):
        self.ai = ai

    def draw_debug(self):
        # return True #temp
        # self.draw_ramps()
        self.draw_expansions()
        # self.draw_unit_info()
        self.draw_turret_placement()
        self.draw_minerals()
        # self.draw_structure_info()
        # self.draw_vision_blockers()
        self.draw_point_list(self.ai.game_info.vision_blockers, color=self.ai.map_manager.vision_blocker_color,
                             text='VB', box_r=1)
        # self.draw_point_list(self.ai.game_info.destructibles, text='DS', box_r=1, color=RED)

    def draw_point_list(self, point_list: List = None, color=None, text=None, box_r=None) -> bool:
        if not color:
            color = GREEN
        if not point_list or (not text and not box_r):
            return True
            # print("cant draw nothing !")

        for p in point_list:
            p = Point2(p)
            h = self.ai.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h))
            if box_r:
                p0 = Point3((pos.x - box_r, pos.y - box_r, pos.z + box_r)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + box_r, pos.y + box_r, pos.z - box_r)) + Point2((0.5, 0.5))
                self.ai.client.debug_box_out(p0, p1, color=color)
            if text:
                self.ai.client.debug_text_world(
                    "\n".join(
                        [
                            f"{text}",

                        ]
                    ),
                    pos,
                    color=color,
                    size=30,
                )

    def draw_unit_info(self):
        for unit in self.ai.units:
            self.ai.client.debug_text_world(
                "\n".join(
                    [
                        f"{unit.type_id.name}:{unit.type_id.value}",
                        f"({unit.position.x},{unit.position.y},{self.ai.game_info.terrain_height[unit.position.rounded]}",

                    ]
                    + [repr(x) for x in unit.orders]
                ),
                unit.position3d,
                color=GREEN,
                size=10,
            )

    def draw_structure_info(self):
        for structure in self.ai.structures:
            self.ai.client.debug_text_world(
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

    def draw_vision_blockers(self):
        vb = self.ai.game_info.vision_blockers
        for p in vb:
            p = Point2(p)
            h2 = self.ai.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            color = Point3((0, 255, 0))
            self.ai.client.debug_box_out(p0, p1, color=color)
            self.ai.client.debug_text_world(
                "\n".join(
                    [
                        f"VB",

                    ]
                ),
                pos,
                color=color,
                size=30,
            )

    def draw_expansion_grid(self, expansion: Expansion, color: Union[Point3, Tuple]):

        if len(expansion.borders) == 0:
            print("shouldn't be here !")
            expansion.set_borders()

        for p in expansion.grid_points:
            p = Point2(p)
            h2 = self.ai.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))

            self.ai.client.debug_box_out(p0, p1, color=color)

    def draw_minerals(self):
        points = [x.position for x in self.ai.mineral_field]
        self.draw_point_list(points, color=self.ai.map_manager.mineral_color, box_r=0.5)

    def draw_expansion_borders(self, color: Union[Point3, Tuple]):
        height_map = self.ai.game_info.terrain_height

        for expansion in self.ai.map_manager.expansions.values():
            height_here = height_map[expansion.coords]
            main_height = height_map[self.ai.start_location.rounded]
            natural_height = height_map[self.ai.main_base_ramp.lower.pop()]  # doesnt matter which
            c = GREEN
            if expansion.coords.rounded == self.ai.start_location.rounded:
                c = GREEN
            elif expansion.coords.rounded.distance_to(self.ai.start_location.rounded) < 33:
                c = BLUE
            else:
                c = RED

            for p in expansion.borders:
                p = Point2(p)
                h2 = self.ai.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
                self.ai.client.debug_box_out(p0, p1, color=c)

    def draw_turret_placement(self):

        for p in self.ai.map_manager.cliffs:
            p = Point2(p)
            h2 = self.ai.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 1, pos.y - 1, pos.z + 2)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 1, pos.y + 1, pos.z - 2)) + Point2((0.5, 0.5))
            color = self.ai.map_manager.turret_color
            # self.ai.client.debug_box_out(p0, p1, color=color)
            self.ai.client.debug_text_world(
                "\n".join(
                    [
                        f"C",
                        f"h:{self.ai.game_info.terrain_height[pos]:.2f}",

                    ]
                ),
                pos,
                color=color,
                size=30,
            )

        # for expansion in self.ai.map_manager.expansions.values():
        #     for p in expansion.turrets:
        #         p = Point2(p)
        #         h2 = self.ai.get_terrain_z_height(p)
        #         pos = Point3((p.x, p.y, h2))
        #         p0 = Point3((pos.x - 1, pos.y - 1, pos.z + 2)) + Point2((0.5, 0.5))
        #         p1 = Point3((pos.x + 1, pos.y + 1, pos.z - 2)) + Point2((0.5, 0.5))
        #         color = self.ai.map_manager.turret_color
        #         self.ai.client.debug_box_out(p0,p1, color=color)
        #         self.ai.client.debug_text_world(
        #             "\n".join(
        #                 [
        #                     f"T",
        #
        #                 ]
        #             ),
        #             pos,
        #             color=color,
        #             size=30,
        #         )

    def draw_placement_grid(self, expansion: Expansion):
        map_area = self.ai.game_info.playable_area
        for (b, a), value in np.ndenumerate(self.ai.game_info.placement_grid.data_numpy):
            # skip non placements which are zero
            if value == 0:
                continue

            # Skip values outside of playable map area
            if not (map_area.x <= a < map_area.x + map_area.width):
                continue
            if not (map_area.y <= b < map_area.y + map_area.height):
                continue

            p = Point2((a, b))
            if expansion.is_in(p):
                h2 = self.ai.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
                color = Point3((0, 255, 0))
                self.ai.client.debug_box_out(p0, p1, color=color)

    def draw_ramps(self):
        for index, ramp in self.ai.map_manager.cached_ramps.items():
            self.ai.map_manager.cached_ramps[index] = ramp

            p = ramp.coords
            c0 = None
            c1 = None
            line_color = Point3((255, 0, 0))
            if p is not None:
                if len(ramp.expansions) > 1:
                    c0 = ramp.expansions[0].coords.to3
                    c1 = ramp.expansions[1].coords.to3

                color = Point3((0, 255, 0))
                h2 = self.ai.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 1.5, pos.y - 1.5, pos.z + 1.5)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + 1.5, pos.y + 1.5, pos.z - 1.5)) + Point2((0.5, 0.5))
                if isinstance(c0, Point3) and isinstance(c1, Point3):
                    self.ai.client.debug_line_out(c0, c1, color=line_color)
                self.ai.client.debug_box_out(p0, p1, color=color)
                self.ai.client.debug_text_world(
                    "\n".join(
                        [
                            f"{ramp.name}",
                            f"Coords: ({p.position.x:.2f},{p.position.y:.2f})",
                        ]
                    ),
                    pos,
                    color=(0, 255, 0),
                    size=12,
                )

    def draw_expansions(self):
        color = GREEN
        self.draw_expansion_borders(color)
        for i, expansion in enumerate(self.ai.map_manager.expansions.values()):
            # if i%2 == 0:
            #     color = Point3((0, 255, 0))
            # else:
            #     color = Point3((255, 0, 0))

            p = expansion.coords
            if isinstance(p, Point2):
                h2 = self.ai.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 2, pos.y - 2, pos.z + 2)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + 2, pos.y + 2, pos.z - 2)) + Point2((0.5, 0.5))
                distance_to_main = p.distance_to(self.ai.start_location.rounded)
                # if distance_to_main < 18.0:
                #     continue

                self.ai.client.debug_box_out(p0, p1, color=color)
                self.ai.client.debug_text_world(
                    "\n".join(
                        [
                            f"{expansion}",
                            f"distance_to_main: {distance_to_main:.2f}",
                            f"Coords: ({p.position.x:.2f},{p.position.y:.2f})",
                            f"Resources: ({len(expansion.resources)})",
                        ]
                    ),
                    pos,
                    color=(0, 255, 255),
                    size=8,
                )

# _game_info.vision_blockers
# _game_info.destructibles
# _game_info.enemy_start_locations
