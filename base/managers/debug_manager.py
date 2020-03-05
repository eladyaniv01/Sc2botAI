from sc2.position import Point3, Point2


class DebugManager:
    def __init__(self, ai=None):
        self.ai = ai

    def draw_debug(self):
        # self.draw_placement_grid()
        self.draw_ramps()
        self.draw_expansions()
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

    def draw_placement_grid(self):
        map_area = self.ai.game_info.playable_area
        for (b, a), value in np.ndenumerate(self.ai.game_info.placement_grid.data_numpy):
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
                if isinstance(c0,Point3) and isinstance(c1, Point3):
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

        for expansion in self.ai.map_manager.expansions.values():
            p = expansion.coords
            if isinstance(p, Point2):
                h2 = self.ai.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                p0 = Point3((pos.x - 2, pos.y - 2, pos.z + 2)) + Point2((0.5, 0.5))
                p1 = Point3((pos.x + 2, pos.y + 2, pos.z - 2)) + Point2((0.5, 0.5))
                distance_to_main = p.distance_to_point2(self.ai.main_base_ramp.depot_in_middle)
                if distance_to_main < 16.0:
                    continue
                color = Point3((0, 255, 0))
                color_zone =Point3((0, 255, 0))
                self.ai.client.debug_sphere_out(p0, 16.8, color=color_zone)
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
                    color=(0, 255, 0),
                    size=12,
                )
