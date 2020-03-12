import math
from math import atan2,degrees
from sc2.position import Point2, Point3


class BaseDriver:
    def __init__(self, ai):
        super().__init__()
        self.ai = ai

    def is_safe_ground(self, my_unit):
        enemies = self.ai.enemy_units.filter(lambda enemy: enemy.can_attack_ground and enemy.distance_to(my_unit) < 10)
        if len(enemies) > 0:
            return False
        return True
