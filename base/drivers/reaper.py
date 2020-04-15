import random
from typing import Union

from sc2 import bot_ai
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2, Point3
from sc2.unit import Unit
import enum
from Sc2botAI.base.drivers.BaseDriver import BaseDriver


class ReaperDriver(BaseDriver):
    def __init__(self, ai: bot_ai = None):
        super().__init__(ai)
        self.ai = ai
        self.condition = UnitTypeId.REAPER
        self.real_init = False
        self.iteration = None
        self.WORKERS = None

    def update_iteration(self):
        self.iteration = self.ai.iteration

    def check_unit(self, unit: Unit) -> bool:
        return unit in set(self.ai.units(self.condition))

    def attack_prime(self, unit: Unit, target: Unit) -> bool:
        if (
            self.WORKERS
        ):  # probably should change this name as it's referring to closest enemy workers to the reaper
            workers = self.WORKERS.filter(lambda unit: unit.distance_to(unit.position) < 20)
            if len(workers) > 0:
                prime_target = min(self.WORKERS, key=lambda x: x.health_percentage)
                self.ai.do(unit.attack(prime_target))
                return True
        self.ai.do(unit.attack(target))
        return True

    async def execute(self) -> bool:
        """
        logic and behavior goes here,
         what will probably end up happening is that
         BaseDriver will be added more methods over
         time as new drivers are created with some semi generic needs
        """
        if not self.real_init:
            self.update_iteration()
            self.real_init = True
        # self.update_sns()
        enemies = self.ai.enemy_units | self.ai.enemy_structures
        enemies_can_attack = enemies.filter(lambda unit: unit.can_attack_ground)

        for r in self.ai.units(UnitTypeId.REAPER):
            assert (
                r.PRIORITY
            ), f"PRIORITY is not set for {r}"  # this breaks when debugger creates a unit
            self.WORKERS = (
                self.ai.enemy_units(UnitTypeId.DRONE)
                | self.ai.enemy_units(UnitTypeId.PROBE)
                | self.ai.enemy_units(UnitTypeId.SCV)
            )
            if len(self.WORKERS) > 0:
                target = min(self.WORKERS, key=lambda x: x.health_percentage)
            else:
                target = None
            # Move the Clients camera to the Trained Unit
            # await self.ai.client.move_camera(r.position)
            # move to range 15 of closest unit if reaper is below 20 hp and not regenerating
            enemy_threats_close = enemies_can_attack.filter(
                lambda unit: unit.distance_to(r) < 15
            )  # threats that can attack the reaper

            if r.health_percentage < 0.3 and enemy_threats_close:
                retreat_points = self.neighbors8(r.position, distance=2) | self.neighbors8(
                    r.position, distance=4
                )
                # filter points that are pathable
                retreat_points = {x for x in retreat_points if self.in_pathing_grid(x)}
                if retreat_points:
                    closest_enemy = enemy_threats_close.closest_to(r)
                    retreat_point = closest_enemy.position.furthest(retreat_points)
                    self.ai.do(r.move(retreat_point))
                    continue  # continue for loop, dont execute any of the following
            enemy_threats_very_close = enemies.filter(
                lambda unit: unit.can_attack_ground and unit.distance_to(r) < 3.5
            )
            # queens_close = enemy_threats_very_close.filter(lambda unit: unit.type_id == UnitTypeId.QUEEN)
            # if len(queens_close) > 0:
            #     print("Queen is close")
            # if r.weapon_cooldown != 0 and queens_close:
            #     if self.ai.iteration % 4 == 0:
            #         closest_queen = queens_close.closest_to(r)
            #         self.ai.do(r.attack(closest_queen))
            #         continue
            # hardcoded attackrange minus 0.5
            # threats that can attack the reaper
            # if r.weapon_cooldown != 0 and enemy_threats_very_close:
            if enemy_threats_very_close:
                if self.ai.iteration % 2 == 0:
                    # if 1 == 1:
                    retreat_points = self.neighbors8(r.position, distance=2) | self.neighbors8(
                        r.position, distance=4
                    )
                    # filter points that are pathable by a reaper
                    retreat_points = {x for x in retreat_points if self.in_pathing_grid(x)}
                    if retreat_points:
                        closest_enemy = enemy_threats_very_close.closest_to(r)
                        retreat_point = max(
                            retreat_points,
                            key=lambda x: x.distance_to(closest_enemy) - x.distance_to(r),
                        )
                        # retreat_point = closest_enemy.position.furthest(retreat_points)
                        self.ai.do(r.move(retreat_point))
                        continue  # continue for loop, don't execute any of the following
            # reaper is ready to attack, shoot nearest ground unit
            enemy_ground_units = enemies.filter(
                lambda unit: unit.distance_to(r) < 5 and not unit.is_flying
            )  # hardcoded attackrange of 5
            if r.weapon_cooldown == 0 and enemy_ground_units:
                enemy_ground_units = enemy_ground_units.sorted(lambda x: x.distance_to(r))
                closest_enemy = enemy_ground_units[0]
                self.attack_prime(r, closest_enemy)
                continue  # continue for loop, dont execute any of the following

            # attack is on cooldown, check if grenade is on cooldown, if not then throw it to furthest closest in range 5
            reaper_grenade_range = self.ai._game_data.abilities[
                AbilityId.KD8CHARGE_KD8CHARGE.value
            ]._proto.cast_range
            enemy_ground_units_in_grenade_range = enemies_can_attack.filter(
                lambda unit: not unit.is_structure
                and not unit.is_flying
                and unit.type_id not in {UnitTypeId.LARVA, UnitTypeId.EGG}
                and unit.distance_to(r) < reaper_grenade_range
            )
            # if enemy_ground_units_in_grenade_range.exists and (r.is_attacking or r.is_moving):
            if enemy_ground_units_in_grenade_range.exists and r.is_attacking:
                # if AbilityId.KD8CHARGE_KD8CHARGE in abilities, we check that to see if the reaper grenade is off cooldown
                abilities = await self.ai.get_available_abilities(r)
                enemy_ground_units_in_grenade_range = enemy_ground_units_in_grenade_range.sorted(
                    lambda x: x.distance_to(r), reverse=True
                )
                furthest_enemy = None
                for enemy in enemy_ground_units_in_grenade_range:
                    if await self.ai.can_cast(
                        r, AbilityId.KD8CHARGE_KD8CHARGE, enemy, cached_abilities_of_unit=abilities,
                    ):
                        furthest_enemy = enemy
                        break
                if furthest_enemy:
                    self.ai.do(r(AbilityId.KD8CHARGE_KD8CHARGE, furthest_enemy))
                    continue  # continue for loop, don't execute any of the following

            # move to nearest closest ground unit/building because no closest unit is closer than 5
            all_enemy_ground_units = self.ai.enemy_units.not_flying
            killed_value_units = self.ai.state.score.killed_value_units
            enemies_can_attack = enemies.filter(lambda unit: unit.can_attack_ground)
            lost_reapers = (
                self.ai.state.score.lost_minerals_army + self.ai.state.score.lost_vespene_army
            )
            if all_enemy_ground_units.exists:
                closest_enemy = all_enemy_ground_units.closest_to(r)
                if r.health_percentage > 0.8:
                    self.ai.do(r.move(closest_enemy))
                continue  # continue for loop, don't execute any of the following
                # move towards to max unit range if closest is closer than 4

            # move to random closest start location if no closest buildings have been seen
            self.seek_and_harass(r)

            if lost_reapers == 0:
                lost_reapers = 1
            # if TAGS.SearchAndDestroy != reaper_driver.tag:
            #     self.ai.do(r.move(random.choice(self.ai.enemy_start_locations)))
            #     reaper_driver.tag = TAGS.SearchAndDestroy

        return True

    # helper functions

    # this checks if a ground unit can walk on a Point2 position
    def in_pathing_grid(self, pos):
        # returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
        assert isinstance(pos, (Point2, Point3, Unit))
        pos = pos.position.to2.rounded
        return self.ai._game_info.pathing_grid[(pos)] != 0

    # stolen and modified from position.py
    def neighbors4(self, position, distance=1):
        p = position
        d = distance
        return {
            Point2((p.x - d, p.y)),
            Point2((p.x + d, p.y)),
            Point2((p.x, p.y - d)),
            Point2((p.x, p.y + d)),
        }

    # stolen and modified from position.py
    def neighbors8(self, position, distance=1):
        p = position
        d = distance
        return self.neighbors4(position, distance) | {
            Point2((p.x - d, p.y - d)),
            Point2((p.x - d, p.y + d)),
            Point2((p.x + d, p.y - d)),
            Point2((p.x + d, p.y + d)),
        }
