from BaseBot import BaseBot
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

ACTION_DO_NOTHING = "donothing"
ACTION_BUILD_SCV = "trainscv"
ACTION_BUILD_SUPPLY_DEPOT = "buildsupplydepot"
ACTION_BUILD_BARRACKS = "buildbarracks"
ACTION_BUILD_MARINE = "buildmarine"
ACTION_ATTACK = "attack"


smart_actions = [
    ACTION_DO_NOTHING,
    ACTION_BUILD_SCV,
    ACTION_BUILD_SUPPLY_DEPOT,
    ACTION_BUILD_BARRACKS,
    ACTION_BUILD_MARINE,
    ACTION_ATTACK,
]


KILL_UNIT_REWARD = 0.3
KILL_BUILDING_REWARD = 0.9
NO_MINERAL_FLOAT_REWARD = 0.5
NO_MINERAL_FLOAT_PENALTY = -0.5
GREATER_FOOD_REWARD = 0.4
GREATER_FOOD_PENALTY = -0.7


# Stolen from https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow


class PickleRick(BaseBot):
    def __init__(self, debug=False):
        super().__init__(debug=debug)
        self.sent_order = False
        # self.qlearn = QLearningTable(actions=list(range(len(smart_actions))))
        self.previous_killed_unit_score = 0
        self.previous_killed_building_score = 0
        self.previous_food_score = 0
        self.previous_minerals = 75
        self.previous_action = None
        self.previous_state = None
        self.action_space_cache = []

    async def on_step(self, iteration):
        await super().on_step(iteration)
        # if not self.units(UnitTypeId.REAPER):
        #     loc = self.main_base_ramp.top_center
        #     await self.client.debug_create_unit([[UnitTypeId.REAPER, 1, loc, 1]])
        # return True
        # training block

        # enemy_units = self.enemy_units
        # enemy_workers = self.enemy_units(UnitTypeId.DRONE)
        # lings = self.enemy_units(UnitTypeId.ZERGLING)
        # queens = self.enemy_units(UnitTypeId.QUEEN)
        # lings = lings | queens
        # good_units = enemy_workers | lings
        #
        # bad_units = [x for x in enemy_units if x not in good_units]
        # bad_flying = [x for x in bad_units if (x.is_flying and x.type_id != UnitTypeId.OVERLORD)]
        # for u in bad_flying:
        #     await self.client.debug_kill_unit(u)
        #
        # if self.iteration % 500 == 0:
        #     for u in bad_units:
        #         await self.client.debug_kill_unit(u)
        # # if self.iteration == 2502:
        # #     await self.client.leave()
        # if not self.units(UnitTypeId.THOR):
        #     await self.client.debug_create_unit(
        #         [[UnitTypeId.THOR, 1, self.main_base_ramp.depot_in_middle, 1]])
        #
        # if not self.units(UnitTypeId.REAPER):
        #
        #     n = 1
        #     loc = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
        #     loc2 = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
        #     loc3 = random.choice(self.enemy_start_locations).towards_with_random_angle(self.game_info.map_center,distance=50)
        #     if self.iteration > 175:
        #         n = 1
        #         await self.client.debug_create_unit(
        #             [[UnitTypeId.REAPER, 1, loc2, 1]])
        #     if self.iteration > 325:
        #         n = 2
        #         await self.client.debug_create_unit(
        #             [[UnitTypeId.REAPER, 1, loc3, 1]])
        #     if self.iteration > 650:
        #         n = 3
        #         await self.client.debug_create_unit(
        #             [[UnitTypeId.REAPER, 1, loc2, 1]])
        #     if self.iteration > 900:
        #         n = 4
        #         await self.client.debug_create_unit(
        #             [[UnitTypeId.REAPER, 2, loc, 1]])
        #
        #
        #     return True
        #
        #     if not self.enemy_units(UnitTypeId.QUEEN):
        #         await self.client.debug_create_unit(
        #             [[UnitTypeId.QUEEN, 1, random.choice(self.enemy_start_locations), 2]])
        #
        # return True

        if (
            self.supply_left < 5
            and self.townhalls.exists
            and self.supply_used >= 14
            and self.can_afford(UnitTypeId.SUPPLYDEPOT)
            and self.structures(UnitTypeId.SUPPLYDEPOT).not_ready.amount
            + self.already_pending(UnitTypeId.SUPPLYDEPOT)
            < 1
        ):
            ws = self.workers.gathering
            if ws:  # if workers found
                w = ws.furthest_to(ws.center)
                loc = await self.find_placement(
                    UnitTypeId.SUPPLYDEPOT, w.position, placement_step=3
                )
                if loc:  # if a placement location was found
                    # build exactly on that location
                    self.do(w.build(UnitTypeId.SUPPLYDEPOT, loc))

        # lower all depots when finished
        for depot in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
            self.do(depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

        # morph commandcenter to orbitalcommand
        if self.structures(UnitTypeId.BARRACKS).ready.exists and self.can_afford(
            UnitTypeId.ORBITALCOMMAND
        ):  # check if orbital is affordable
            for cc in self.townhalls(
                UnitTypeId.COMMANDCENTER
            ).idle:  # .idle filters idle command centers
                self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))

        # expand if we can afford and have less than 2 bases
        if (
            1 <= self.townhalls.amount < 2
            and self.already_pending(UnitTypeId.COMMANDCENTER) == 0
            and self.can_afford(UnitTypeId.COMMANDCENTER)
        ):
            # get_next_expansion returns the center of the mineral fields of the next nearby expansion
            next_expo = await self.get_next_expansion()
            # from the center of mineral fields, we need to find a valid place to place the command center
            location = await self.find_placement(
                UnitTypeId.COMMANDCENTER, next_expo, placement_step=1
            )
            if location:
                # now we "select" (or choose) the nearest worker to that found location
                w = self.select_build_worker(location)
                if w and self.can_afford(UnitTypeId.COMMANDCENTER):
                    # the worker will be commanded to build the command center
                    self.do(w.build(UnitTypeId.COMMANDCENTER, location))

        # make up to 4 barracks if we can afford them
        # check if we have a supply depot (tech requirement) before trying to make barracks
        if (
            self.structures.of_type(
                [UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTLOWERED, UnitTypeId.SUPPLYDEPOTDROP,]
            ).ready.exists
            and self.structures(UnitTypeId.BARRACKS).amount
            + self.already_pending(UnitTypeId.BARRACKS)
            < 4
            and self.can_afford(UnitTypeId.BARRACKS)
        ):
            ws = self.workers.gathering
            if (
                ws and self.townhalls.exists
            ):  # need to check if townhalls.amount > 0 because placement is based on townhall location
                w = ws.furthest_to(ws.center)
                # I chose placement_step 4 here so there will be gaps between barracks hopefully
                loc = await self.find_placement(
                    UnitTypeId.BARRACKS, self.townhalls.random.position, placement_step=4,
                )
                if loc:
                    self.do(w.build(UnitTypeId.BARRACKS, loc))

        # build refineries (on nearby vespene) when at least one barracks is in construction
        if (
            self.structures(UnitTypeId.BARRACKS).amount > 0
            and self.already_pending(UnitTypeId.REFINERY) < 1
        ):
            for th in self.townhalls:
                vgs = self.vespene_geyser.closer_than(10, th)
                for vg in vgs:
                    if await self.can_place(UnitTypeId.REFINERY, vg.position) and self.can_afford(
                        UnitTypeId.REFINERY
                    ):
                        ws = self.workers.gathering
                        if ws.exists:  # same condition as above
                            w = ws.closest_to(vg)
                            # caution: the target for the refinery has to be the vespene geyser, not its position!
                            self.do(w.build(UnitTypeId.REFINERY, vg))

        # make scvs until 18, usually you only need 1:1 mineral:gas ratio for reapers, but if you don't lose any then you will need additional depots (mule income should take care of that)
        # stop scv production when barracks is complete but we still have a command cender (priotize morphing to orbital command)
        if (
            self.can_afford(UnitTypeId.SCV)
            and self.supply_left > 0
            and self.workers.amount < 18
            and (
                self.structures(UnitTypeId.BARRACKS).ready.amount < 1
                and self.townhalls(UnitTypeId.COMMANDCENTER).idle.exists
                or self.townhalls(UnitTypeId.ORBITALCOMMAND).idle.exists
            )
        ):
            for th in self.townhalls.idle:
                self.do(th.train(UnitTypeId.SCV))

        # make reapers if we can afford them and we have supply remaining
        if self.can_afford(UnitTypeId.REAPER) and self.supply_left > 0:
            # loop through all idle barracks
            for rax in self.structures(UnitTypeId.BARRACKS).idle:
                self.do(rax.train(UnitTypeId.REAPER))

        # send workers to mine from gas
        if self.iteration % 25 == 0:
            await self.distribute_workers()

        # reaper micro

        # for r in self.unitsT(UnitTypeId.REAPER):
        #     # move to random closest start location if no closest buildings have been seen
        #     self.do(r.move(random.choice(self.enemy_start_locations)))

        # manage idle scvs, would be taken care by distribute workers aswell
        if self.townhalls.exists:
            for w in self.workers.idle:
                th = self.townhalls.closest_to(w)
                mfs = self.mineral_field.closer_than(10, th)
                if mfs:
                    mf = mfs.closest_to(w)
                    self.do(w.gather(mf))

        # manage orbital energy and drop mules
        for oc in self.townhalls(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mfs = self.mineral_field.closer_than(10, oc)
            if mfs:
                mf = max(mfs, key=lambda x: x.mineral_contents)
                self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))

        # when running out of mineral fields near command center, fly to next base with minerals

    # helper functions

    # this checks if a ground unit can walk on a Point2 position
    def inPathingGrid(self, pos):
        # returns True if it is possible for a ground unit to move to pos - doesnt seem to work on ramps or near edges
        assert isinstance(pos, (Point2, Point3, Unit))
        pos = pos.position.to2.rounded
        return self._game_info.pathing_grid[(pos)] != 0

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

    # already pending function rewritten to only capture unitsT in queue and queued buildings
    # the difference to bot_ai.py alredy_pending() is: it will not cover structures in construction
    def already_pending(self, unit_type):
        ability = self._game_data.units[unit_type.value].creation_ability
        unitAttributes = self._game_data.units[unit_type.value].attributes

        buildings_in_construction = self.structures(unit_type).not_ready
        if 8 not in unitAttributes and any(
            o.ability == ability for w in (self.units) for o in w.orders
        ):
            return sum(
                [o.ability == ability for w in (self.units - self.workers) for o in w.orders]
            )
        # following checks for unit production in a building queue, like queen, also checks if hatch is morphing to LAIR
        elif any(o.ability.id == ability.id for w in (self.structures) for o in w.orders):
            return sum([o.ability.id == ability.id for w in (self.structures) for o in w.orders])
        # the following checks if a worker is about to start a construction (and for scvs still constructing if not checked for structures with same position as target)
        elif any(o.ability == ability for w in self.workers for o in w.orders):
            return (
                sum([o.ability == ability for w in self.workers for o in w.orders])
                - buildings_in_construction.amount
            )
        elif any(egg.orders[0].ability == ability for egg in self.units(UnitTypeId.EGG)):
            return sum([egg.orders[0].ability == ability for egg in self.units(UnitTypeId.EGG)])
        return 0

    # distribute workers function rewritten, the default distribute_workers() function did not saturate gas quickly enough
    async def distribute_workers(self, performanceHeavy=True, onlySaturateGas=False):
        # expansion_locations = self.expansion_locations
        # owned_expansions = self.owned_expansions

        mineralTags = [x.tag for x in self.mineral_field]
        # gasTags = [x.tag for x in self.state.unitsT.vespene_geyser]
        gas_buildingTags = [x.tag for x in self.gas_buildings]

        workerPool = self.units & []
        workerPoolTags = set()

        # find all gas_buildings that have surplus or deficit
        deficit_gas_buildings = {}
        surplusgas_buildings = {}
        for g in self.gas_buildings.filter(lambda x: x.vespene_contents > 0):
            # only loop over gas_buildings that have still gas in them
            deficit = g.ideal_harvesters - g.assigned_harvesters
            if deficit > 0:
                deficit_gas_buildings[g.tag] = {"unit": g, "deficit": deficit}
            elif deficit < 0:
                surplusWorkers = self.workers.closer_than(10, g).filter(
                    lambda w: w not in workerPoolTags
                    and len(w.orders) == 1
                    and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER]
                    and w.orders[0].target in gas_buildingTags
                )
                # workerPool.extend(surplusWorkers)
                for i in range(-deficit):
                    if surplusWorkers.amount > 0:
                        w = surplusWorkers.pop()
                        workerPool.append(w)
                        workerPoolTags.add(w.tag)
                surplusgas_buildings[g.tag] = {"unit": g, "deficit": deficit}

        # find all townhalls that have surplus or deficit
        deficitTownhalls = {}
        surplusTownhalls = {}
        if not onlySaturateGas:
            for th in self.townhalls:
                deficit = th.ideal_harvesters - th.assigned_harvesters
                if deficit > 0:
                    deficitTownhalls[th.tag] = {"unit": th, "deficit": deficit}
                elif deficit < 0:
                    surplusWorkers = self.workers.closer_than(10, th).filter(
                        lambda w: w.tag not in workerPoolTags
                        and len(w.orders) == 1
                        and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER]
                        and w.orders[0].target in mineralTags
                    )
                    # workerPool.extend(surplusWorkers)
                    for i in range(-deficit):
                        if surplusWorkers.amount > 0:
                            w = surplusWorkers.pop()
                            workerPool.append(w)
                            workerPoolTags.add(w.tag)
                    surplusTownhalls[th.tag] = {"unit": th, "deficit": deficit}

            if all(
                [
                    len(deficit_gas_buildings) == 0,
                    len(surplusgas_buildings) == 0,
                    len(surplusTownhalls) == 0 or deficitTownhalls == 0,
                ]
            ):
                # cancel early if there is nothing to balance
                return

        # check if deficit in gas less or equal than what we have in surplus, else grab some more workers from surplus bases
        deficitGasCount = sum(
            gasInfo["deficit"]
            for gasTag, gasInfo in deficit_gas_buildings.items()
            if gasInfo["deficit"] > 0
        )
        surplusCount = sum(
            -gasInfo["deficit"]
            for gasTag, gasInfo in surplusgas_buildings.items()
            if gasInfo["deficit"] < 0
        )
        surplusCount += sum(
            -thInfo["deficit"]
            for thTag, thInfo in surplusTownhalls.items()
            if thInfo["deficit"] < 0
        )

        if deficitGasCount - surplusCount > 0:
            # grab workers near the gas who are mining minerals
            for gTag, gInfo in deficit_gas_buildings.items():
                if workerPool.amount >= deficitGasCount:
                    break
                workersNearGas = self.workers.closer_than(10, gInfo["unit"]).filter(
                    lambda w: w.tag not in workerPoolTags
                    and len(w.orders) == 1
                    and w.orders[0].ability.id in [AbilityId.HARVEST_GATHER]
                    and w.orders[0].target in mineralTags
                )
                while workersNearGas.amount > 0 and workerPool.amount < deficitGasCount:
                    w = workersNearGas.pop()
                    workerPool.append(w)
                    workerPoolTags.add(w.tag)

        # now we should have enough workers in the pool to saturate all gases, and if there are workers left over, make them mine at townhalls that have mineral workers deficit
        for gTag, gInfo in deficit_gas_buildings.items():
            if performanceHeavy:
                # sort furthest away to closest (as the pop() function will take the last element)
                workerPool.sort(key=lambda x: x.distance_to(gInfo["unit"]), reverse=True)
            for i in range(gInfo["deficit"]):
                if workerPool.amount > 0:
                    w = workerPool.pop()
                    if len(w.orders) == 1 and w.orders[0].ability.id in [AbilityId.HARVEST_RETURN]:
                        self.do(w.gather(gInfo["unit"], queue=True))
                    else:
                        self.do(w.gather(gInfo["unit"]))

        if not onlySaturateGas:
            # if we now have left over workers, make them mine at bases with deficit in mineral workers
            for thTag, thInfo in deficitTownhalls.items():
                if performanceHeavy:
                    # sort furthest away to closest (as the pop() function will take the last element)
                    workerPool.sort(key=lambda x: x.distance_to(thInfo["unit"]), reverse=True)
                for i in range(thInfo["deficit"]):
                    if workerPool.amount > 0:
                        w = workerPool.pop()
                        mf = self.mineral_field.closer_than(10, thInfo["unit"]).closest_to(w)
                        if len(w.orders) == 1 and w.orders[0].ability.id in [
                            AbilityId.HARVEST_RETURN
                        ]:
                            self.do(w.gather(mf, queue=True))
                        else:
                            self.do(w.gather(mf))


def main():
    map = random.choice(
        [
            "AbyssalReefLE",
            "AcropolisLE",
            "AutomatonLE",
            "BelShirVestigeLE",
            "CactusValleyLE",
            "CyberForestLE",
            "DiscoBloodbathLE",
            "EphemeronLE",
            "HonorgroundsLE",
            "KairosJunctionLE",
            "KingsCoveLE",
            "NewkirkPrecinctTE",
            "NewRepugnancyLE",
            "PaladinoTerminalLE",
            "PortAleksanderLE",
            "ProximaStationLE",
            "ThunderbirdLE",
            "TritonLE",
            "WintersGateLE",
            "WorldofSleepersLE",
            "YearZeroLE",
        ]
    )

    map = "AbyssalReefLE"
    sc2.run_game(
        sc2.maps.get(map),
        [Bot(Race.Terran, PickleRick(debug=True)), Computer(Race.Zerg, Difficulty.Hard),],
        realtime=False,
        # sc2_version="4.10.1",
    )


if __name__ == "__main__":
    for i in range(1):
        print(f"i = {i}")
        main()
