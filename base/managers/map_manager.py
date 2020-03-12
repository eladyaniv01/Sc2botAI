from collections import namedtuple
from typing import Union

from Sc2botAI.base.Expansion import Expansion
from Sc2botAI.base.RampExt import RampExt
from sc2.position import Point3, Point2

# ExpansionTuple = namedtuple("Expansion", ["name", "coords", "resources", "ramp"])


# TODO base manager for all managers
# TODO identify rocks,  choke points,  high ground strategic points and the area they are superior to

class MapManager:

    def __init__(self, ai=None):
        self.ai = ai
        self.cached_ramps = {}
        self.expansions = {}
        self._solved = False
        self.townhall_color = Point3((200, 170, 55)) #gold
        self.building_color = Point3((255, 0, 0)) #red
        self.depot_color = Point3((55, 255, 200)) #lBlue
        self.turret_color = Point3((0, 0, 255))
        self.mineral_color = Point3((55, 200, 255)) #blue
        self.gas_color = Point3((0, 155, 0)) # green
        self.empty_color = Point3((255, 255, 255)) #white
        self.not_buildable_color = Point3((0, 0, 0)) #black
        self.ramp_color = Point3((139, 0, 0)) # brown
        self.vision_blocker_color = Point3((139, 0, 80)) #purple


    def solve_ramps(self):
        for index, ramp in enumerate(self.ai.game_info.map_ramps):
            self.cached_ramps[index] = RampExt(ramp=ramp, index=index)

    def solve_expansions(self):
        if not self.ai:
            print("Seems like this manager is not connected to any ai")
            return True
        self.solve_ramps()
        expansion_dict = sorted(self.ai.expansion_locations.items(),
                                key=lambda x: x[0].distance_to_point2(list(self.ai.main_base_ramp.points)[0]),
                                reverse=False)

        for index, info in enumerate(expansion_dict):
            expansion = Expansion(
                ai=self.ai,
                index=index,
                coords=info[0],
                resources=info[1],
                ramps=self.get_exp_ramps(info[0])
            )
            self.expansions[index] = expansion
            expansion.set_borders()

            [ramp.expansions.append(expansion) for ramp in expansion.ramps]

        self._solved = True

    def get_exp_ramps(self, coords=None):
        if not coords:
            return False
        exp_list = list(self.expansions.values())
        expansions = [x for x in filter(lambda x: x.coords == coords, exp_list)]
        d = {}
        for ramp_ext in self.cached_ramps.values():
            d[ramp_ext] = ramp_ext.coords.manhattan_distance(coords)
            for exp in expansions:
                ramp_ext.expansions.append(exp)
        tmp = d.copy()
        closest = min(tmp, key=tmp.get)
        del tmp[closest]
        second_closest = min(tmp, key=tmp.get)
        distance = closest.coords.manhattan_distance(second_closest.coords)
        if distance < 30:
            return [closest, second_closest]
        return [closest]

    def __repr__(self):
        return f'<ExpansionManager: {self.ai}>'
