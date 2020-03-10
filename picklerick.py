from Sc2botAI.BaseBot import BaseBot
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


class PickleRick(BaseBot):
    def __init__(self, debug = False):
        super().__init__(debug=debug)
        self.sent_order = False

    async def on_step(self, iteration):
        await super().on_step(iteration)
        ccs = self.townhalls(COMMANDCENTER)
        if not ccs:
            return
        else:
            cc = ccs.first

        await self.distribute_workers()
        if not self.structures(BARRACKS):
            await self.client.debug_create_unit([[UnitTypeId.BARRACKS,1, self.main_base_ramp.barracks_correct_placement,1]])
        if self.can_afford(SCV) and self.workers.amount < 16 and cc.is_idle:
            self.do(cc.train(SCV), subtract_cost=True, subtract_supply=True)

        # Raise depos when enemies are nearby
        for depo in self.structures(SUPPLYDEPOT).ready:
            for unit in self.enemy_units:
                if unit.distance_to(depo) < 15:
                    break
            else:
                self.do(depo(MORPH_SUPPLYDEPOT_LOWER))

        # Lower depos when no enemies are nearby
        for depo in self.structures(SUPPLYDEPOTLOWERED).ready:
            for unit in self.enemy_units:
                if unit.distance_to(depo) < 10:
                    self.do(depo(MORPH_SUPPLYDEPOT_RAISE))
                    break

        # Draw ramp points
        self.draw_ramp_points()
        if self.structures(UnitTypeId.ENGINEERINGBAY).amount > 0 and not self.already_pending(UnitTypeId.ENGINEERINGBAY) > 0:
            # print(f"len turret queue : {len(self.map_manager.expansions[0].turret_queue)}")
            q = self.map_manager.expansions[1].turret_queue
            if len(q) and not self.already_pending(UnitTypeId.MISSILETURRET):
                turret_position = Point2(q.pop())

                await self.build(UnitTypeId.MISSILETURRET,near=turret_position)
            # else:
            #     print("no turret queue")


                # self.map_manager.expansions[0].turrets = iter(list(self.map_manager.expansions[0].turrets))
                # for turret_position in self.map_manager.expansions[0].turrets.__next__():
                #     await self.build(UnitTypeId.MISSILETURRET, near=Point2(turret_position))

        # # Draw pathing grid
        # self.draw_pathing_grid()

        # Draw placement  grid
        # self.draw_placement_grid()

        # Draw vision blockers
        # self.draw_vision_blockers()

        # Draw visibility pixelmap for debugging purposes
        # self.draw_visibility_pixelmap()

        # Draw some example boxes around units, lines towards command center, text on the screen and barracks
        # self.draw_example()

        # Draw if two selected units are facing each other - green if this guy is facing the other, red if he is not
        # self.draw_facing_units()

        depot_placement_positions = self.main_base_ramp.corner_depots
        # Uncomment the following if you want to build 3 supply depots in the wall instead of a barracks in the middle + 2 depots in the corner
        # depot_placement_positions = self.main_base_ramp.corner_depots | {self.main_base_ramp.depot_in_middle}

        barracks_placement_position = self.main_base_ramp.barracks_in_middle
        # If you prefer to have the barracks in the middle without room for addons, use the following instead
        # barracks_placement_position = self.main_base_ramp.barracks_in_middle

        depots = self.structures.of_type({SUPPLYDEPOT, SUPPLYDEPOTLOWERED})

        # Filter locations close to finished supply depots
        if depots:
            depot_placement_positions = {d for d in depot_placement_positions if depots.closest_distance_to(d) > 1}

        # Build depots
        if self.can_afford(SUPPLYDEPOT) and self.already_pending(SUPPLYDEPOT) == 0:
            if len(depot_placement_positions) == 0:
                return
            # Choose any depot location
            target_depot_location = depot_placement_positions.pop()
            ws = self.workers.gathering
            if ws:  # if workers were found
                w = ws.random
                self.do(w.build(SUPPLYDEPOT, target_depot_location))

        # Build barracks
        if depots.ready and self.can_afford(BARRACKS):
            # if self.structures(BARRACKS).amount + self.already_pending(BARRACKS) > 0:
            #     return
            if not self.structures(BARRACKS):
                await self.client.debug_create_unit([[UnitTypeId.BARRACKS,1, Point2((149,112))]])
                ws = self.workers.gathering
                if ws and barracks_placement_position:  # if workers were found
                    w = ws.random
                    self.do(w.build(BARRACKS, barracks_placement_position))

        marines: Units = self.units(UnitTypeId.MARINE).idle
        if marines.amount > 15:
            target = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
            for marine in marines:
                self.do(marine.attack(target))

        # Train more SCVs
        if self.can_afford(UnitTypeId.SCV) and self.supply_workers < 16 and cc.is_idle:
            self.do(cc.train(UnitTypeId.SCV), subtract_supply=True, subtract_cost=True)

        # Build more depots
        elif (self.supply_left < (2 if self.structures(UnitTypeId.BARRACKS).amount < 3 else 4) and self.supply_used >= 14):
            if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
                target_depot_location = depot_placement_positions.pop()
                await self.build(UnitTypeId.SUPPLYDEPOT, near=target_depot_location)
        # Train marines
        # print(f" raxs = {self.structures(UnitTypeId.BARRACKS)}")
        # print(f" idle = {self.structures(UnitTypeId.BARRACKS).ready.idle}")
        for rax in self.structures(UnitTypeId.BARRACKS).ready.idle:
            if self.can_afford(UnitTypeId.MARINE):
                self.do(rax.train(UnitTypeId.MARINE), subtract_supply=True, subtract_cost=True)
                # print("got here")

        # Send idle workers to gather minerals near command center
        for scv in self.workers.idle:
            self.do(scv.gather(self.mineral_field.closest_to(cc)))

        if self.structures(UnitTypeId.ENGINEERINGBAY).amount < 1:
            if self.can_afford(UnitTypeId.ENGINEERINGBAY):
                await self.build(UnitTypeId.ENGINEERINGBAY, near=cc.position.towards(self.game_info.map_center, 5))

    async def on_building_construction_started(self, unit: Unit):
        print(f"Construction of building {unit} started at {unit.position}.")

    async def on_building_construction_complete(self, unit: Unit):
        print(f"Construction of building {unit} completed at {unit.position}.")

    async def on_enemy_unit_entered_vision(self, unit: Unit):
        print(f" {unit} entered vision at {unit.position}.")

    def draw_ramp_points(self):
        for ramp in self.game_info.map_ramps:
            for p in ramp.points:
                h2 = self.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                color = Point3((255, 0, 0))
                if p in ramp.upper:
                    color = Point3((0, 255, 0))
                if p in ramp.upper2_for_ramp_wall:
                    color = Point3((0, 255, 255))
                if p in ramp.lower:
                    color = Point3((0, 0, 255))
                self._client.debug_box2_out(pos, half_vertex_length=0.25, color=color)
                # Identical to above:
                # p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25))
                # p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25))
                # print(f"Drawing {p0} to {p1}")
                # self._client.debug_box_out(p0, p1, color=color)

    def draw_pathing_grid(self):
        map_area = self._game_info.playable_area
        for (b, a), value in np.ndenumerate(self._game_info.pathing_grid.data_numpy):
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

    def draw_vision_blockers(self):
        for p in self.game_info.vision_blockers:
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # print(f"Drawing {p0} to {p1}")
            color = Point3((255, 0, 0))
            self._client.debug_box_out(p0, p1, color=color)

    def draw_visibility_pixelmap(self):
        for (y, x), value in np.ndenumerate(self.state.visibility.data_numpy):
            p = Point2((x, y))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # Red
            color = Point3((255, 0, 0))
            # If value == 2: show green (= we have vision on that point)
            if value == 2:
                color = Point3((0, 255, 0))
            self._client.debug_box_out(p0, p1, color=color)

    def draw_example(self):
        # Draw green boxes around SCVs if they are gathering, yellow if they are returning cargo, red the rest
        scv: Unit
        for scv in self.workers:
            pos = scv.position3d
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25))
            # Red
            color = Point3((255, 0, 0))
            if scv.is_gathering:
                color = Point3((0, 255, 0))
            elif scv.is_returning:
                color = Point3((255, 255, 0))
            self._client.debug_box_out(p0, p1, color=color)

        # Draw lines from structures to command center
        if self.townhalls:
            cc = self.townhalls[0]
            p0 = cc.position3d
            structure: Unit
            for structure in self.structures:
                if structure == cc:
                    continue
                p1 = structure.position3d
                # Red
                color = Point3((255, 0, 0))
                self._client.debug_line_out(p0, p1, color=color)

            # Draw text on barracks
            if structure.type_id == UnitTypeId.BARRACKS:
                # Blue
                color = Point3((0, 0, 255))
                pos = structure.position3d + Point3((0, 0, 0.5))
                # TODO: Why is this text flickering
                self._client.debug_text_world(text="MY RAX", pos=pos, color=color, size=16)

        # Draw text in top left of screen
        self._client.debug_text_screen(text="Hello world!", pos=Point2((0, 0)), color=None, size=16)
        self._client.debug_text_simple(text="Hello world2!")

    def draw_facing_units(self):
        """ Draws green box on top of selected_unit2, if selected_unit2 is facing selected_unit1 """
        selected_unit1: Unit
        selected_unit2: Unit
        red = Point3((255, 0, 0))
        green = Point3((0, 255, 0))
        for selected_unit1 in (self.units | self.structures).selected:
            for selected_unit2 in self.units.selected:
                if selected_unit1 == selected_unit2:
                    continue
                if selected_unit2.is_facing_unit(selected_unit1):
                    self._client.debug_box2_out(selected_unit2, half_vertex_length=0.25, color=green)
                else:
                    self._client.debug_box2_out(selected_unit2, half_vertex_length=0.25, color=red)

def main():
    map = random.choice(
        [
            'AbyssalReefLE',
            'AcropolisLE',
            'AutomatonLE',
            'BelShirVestigeLE',
            'CactusValleyLE',
            'CyberForestLE',
            'DiscoBloodbathLE',
            'EphemeronLE',
            'HonorgroundsLE',
            'KairosJunctionLE',
            'KingsCoveLE',
            'Ladder2019Season3',
            'NewkirkPrecinctTE',
            'NewRepugnancyLE',
            'PaladinoTerminalLE',
            'PortAleksanderLE',
            'ProximaStationLE',
            'ThunderbirdLE',
            'TritonLE',
            'WintersGateLE',
            'WorldofSleepersLE',
            'YearZeroLE'

        ]
    )
    # map = "ParaSiteLE"
    sc2.run_game(
        sc2.maps.get(map),
        [Bot(Race.Terran, PickleRick(debug = True)), Computer(Race.Zerg, Difficulty.Easy)],
        realtime=False,
        # sc2_version="4.10.1",
    )

if __name__ == "__main__":
    main()