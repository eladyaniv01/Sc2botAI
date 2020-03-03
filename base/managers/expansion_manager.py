
from collections import namedtuple

ExpansionTuple = namedtuple("Expansion", ["name", "coords", "resources"])


class ExpansionManager:

    def __init__(self, ai=None):
        self.ai = ai
        self.expansions = {}
        self._solved = False

    def solve_expansions(self):
        if self._solved:
            return True
        if not self.ai:
            print("Seems like this manager is not connected to any ai")
            return True

        expansion_dict = sorted(self.ai.expansion_locations.items(),
                                key=lambda  x:x[0].distance_to_point2(self.ai.main_base_ramp.depot_in_middle), reverse=False)

        for index, info in enumerate(expansion_dict):
            expansion_tuple = ExpansionTuple(index,info[0],info[1])
            self.expansions[index] = expansion_tuple



        self._solved = True