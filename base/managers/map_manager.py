from collections import namedtuple
from Sc2botAI.base.common import Expansion, RampExt

ExpansionTuple = namedtuple("Expansion", ["name", "coords", "resources", "ramp"])


# TODO base manager for all managers
# TODO identify rocks,  choke points,  high ground strategic points and the area they are superior to

class MapManager:

    def __init__(self, ai=None):
        self.ai = ai
        self.cached_ramps = {}
        self.expansions = {}
        self._solved = False

    def solve_ramps(self):
        for index, ramp in enumerate(self.ai.game_info.map_ramps):
            self.cached_ramps[index] = RampExt(ramp=ramp, index=index)

    def solve_expansions(self):
        if self._solved:
            return True
        if not self.ai:
            print("Seems like this manager is not connected to any ai")
            return True
        self.solve_ramps()
        expansion_dict = sorted(self.ai.expansion_locations.items(),
                                key=lambda x: x[0].distance_to_point2(self.ai.main_base_ramp.depot_in_middle),
                                reverse=False)

        for index, info in enumerate(expansion_dict):
            expansion = Expansion(
                index=index,
                coords=info[0],
                resources=info[1],
                ramps=self.get_exp_ramps(info[0])
            )
            self.expansions[index] = expansion

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
