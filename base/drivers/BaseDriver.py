import enum
import random
from typing import List, Union
from sc2.unit import Unit
from sc2 import bot_ai
from sc2.ids.unit_typeid import UnitTypeId


class UnitPriority(enum.Enum):
    New = (0,)
    Idle = (1,)
    Defending = (
        2,
    )  # TODO   defending what ? some method to link Role with expansions or key locations
    Attacking = (
        3,
    )  # TODO   Attacking what ? some method to link Role with expansions or key locations
    Harassing = (
        4,
    )  # TODO   Harassing what ? some method to link Role with expansions or key locations
    Scouting = (
        4,
    )  # TODO   Scouting what ? some method to link Role with expansions or key locations


class BaseDriver:
    def __init__(self, ai: bot_ai = None):
        super().__init__()
        self.ai = ai
        self.targets = []

    def is_safe_ground(self, my_unit: Unit) -> bool:
        enemies = self.ai.enemy_units.filter(
            lambda enemy: enemy.can_attack_ground and enemy.distance_to(my_unit) < 10
        )
        if len(enemies) > 0:
            return False
        return True

    def seek_and_harass(
        self, unit: Unit
    ) -> bool:  # for harassing not sure if this should return bool or not, or anything
        enemy_workers = (
            self.ai.enemy_units(UnitTypeId.DRONE)
            | self.ai.enemy_units(UnitTypeId.PROBE)
            | self.ai.enemy_units(UnitTypeId.SCV)
        )
        if len(enemy_workers) > 0:
            self.ai.do(unit.attack(random.choice(enemy_workers)))
        else:
            try:
                loc = random.choice(self.ai.enemy_start_locations).towards_with_random_angle(
                    self.ai.game_info.map_center, distance=5
                )
                self.ai.do(unit.move(loc))
            except Exception as e:
                print(e)
                print("this is not a ladder map,  adjusting...")
                loc = random.choice(
                    list(self.ai.expansion_locations.keys())
                ).towards_with_random_angle(self.ai.game_info.map_center, distance=5)
                self.ai.do(unit.move(loc))

        return True
