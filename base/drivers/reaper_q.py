import random
import math


import numpy as np
import pandas as pd
import random

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units
import enum
from qlearningtable import QLearningTable
import enum
from Sc2botAI.base.drivers.BaseDriver import BaseDriver
QFILE = "reaper_q_driver.pickle"

# TODO generic training map with adjustable configuration (ie spawn units in middle,  spawn structures,  rules)
# TODO move qlearning table to a generic place for others qagents to import from
# Stolen from https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow
class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions  # a list
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        # action selection
        if np.random.uniform() < self.epsilon:
            # choose best action
            state_action = self.q_table.loc[observation, :]
            # some actions may have the same value, randomly choose on in these actions
            action = np.random.choice(state_action[state_action == np.max(state_action)].index)
        else:
            # choose random action
            action = np.random.choice(self.actions)
        return action

    def learn(self, s, a, r, s_):
        self.check_state_exist(s_)
        q_predict = self.q_table.loc[s, a]
        if s_ != 'terminal':
            q_target = r + self.gamma * self.q_table.loc[s_, :].max()  # next state is not terminal
        else:
            q_target = r  # next state is terminal
        self.q_table.loc[s, a] += self.lr * (q_target - q_predict)  # update

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            self.q_table = self.q_table.append(
                pd.Series(
                    [0] * len(self.actions),
                    index=self.q_table.columns,
                    name=state,
                )
            )


class Policy(enum.Enum):
    Passive = 0,
    Offensive = 1,


class GridMover:
    def __init__(self, ai, unit):
        self.ai = ai
        self.unit = unit
        self.loc = unit.position

    def move_right(self):
        step = Point2((1, 0))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def move_left(self):
        step = Point2((-1, 0))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def move_up(self):
        step = Point2((0, 1))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def move_up_right(self):
        step = Point2((1, 1))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def move_up_left(self):
        step = Point2((-1, 1))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def move_down(self):
        step = Point2((0, -1))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def move_down_right(self):
        step = Point2((1, -1))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def move_down_left(self):
        step = Point2((-1, -1))
        self.ai.do(self.unit.smart(self.loc.offset(step)))
        self.loc = self.loc.offset(step)
        return True

    def attack(self, closest=None):
        if not closest:
            self.ai.do(self.unit.move(random.choice(self.ai.enemy_start_locations)))
            return True
        if isinstance(closest, Units):
            closest = closest.closest_to(self.unit)

        self.ai.do(self.unit.attack(closest))
        return True

    def attack_weakest(self, weakest=None):
        if weakest:
            self.ai.do(self.unit.attack(weakest))
        else:
            return True

    def attack_throw_grenade(self, weakest=None, closest=None):
        target = weakest or closest

        if isinstance(target, Units):
            target = target.closest_to(self.unit)

        self.ai.do(self.unit(AbilityId.KD8CHARGE_KD8CHARGE, target))
        return True


LOST_REAPER_PENALTY = -3
STRUCTUE_KILL_REWARD = 1
UNIT_KILL_REWARD = 0.7
DAMAGE_REWARD = 0.1
DAMAGE_PENALTY = -0.05

ACTION_DO_NOTHING = 'donothing'
ACTION_MOVE_UP = 'moveup'
ACTION_MOVE_DOWN = 'movedown'
ACTION_MOVE_LEFT = 'moveleft'
ACTION_MOVE_RIGHT = 'moveright'
ACTION_MOVE_UP_RIGHT = 'moveupright'
ACTION_MOVE_UP_LEFT = 'moveupleft'
ACTION_MOVE_DOWN_LEFT = 'movedownleft'
ACTION_MOVE_DOWN_RIGHT = 'movedownright'
ACTION_ATTACK_CLOSEST_ENEMY = 'attackclosestenemy'
ACTION_ATTACK_WEAKEST_ENEMY = 'attackweakestenemy'
ACTION_ATTACK_THROW_GRENADE = 'attackthrowgrenadeclosestenemy'

smart_actions = [
    ACTION_DO_NOTHING,
    ACTION_MOVE_UP,
    ACTION_MOVE_DOWN,
    ACTION_MOVE_LEFT,
    ACTION_MOVE_RIGHT,
    ACTION_MOVE_UP_RIGHT,
    ACTION_MOVE_UP_LEFT,
    ACTION_MOVE_DOWN_LEFT,
    ACTION_MOVE_DOWN_RIGHT,
    ACTION_ATTACK_CLOSEST_ENEMY,
    ACTION_ATTACK_WEAKEST_ENEMY,
    ACTION_ATTACK_THROW_GRENADE,

]


class ReaperQAgent(BaseDriver):
    def __init__(self, ai=None, qtable=None, unit=None):
        super().__init__(ai=ai)
        self.qlearn = qtable or QLearningTable(actions=list(range(len(smart_actions))))
        self.unit = unit
        self.condition = UnitTypeId.REAPER
        self.lost_reapers = 0
        self.last_killed_value_units = 0
        self.last_structures_dmg = 0
        self.last_army_dmg = 0
        self.last_dmg_dealt = 0
        self.reaper_count = 1
        self.previous_action = None
        self.previous_state = None
        self.action_space_cache = []
        self.policy = Policy.Passive

    async def do_(self, unit, smart_action, enemies_can_attack=None):
        closest = enemies_can_attack.sorted(lambda x: x.distance_to(unit))
        weakest = enemies_can_attack.sorted(lambda x: x.health)
        reaper_grenade_range = self.ai._game_data.abilities[AbilityId.KD8CHARGE_KD8CHARGE.value]._proto.cast_range
        enemy_ground_units_in_grenade_range = enemies_can_attack.filter(
            lambda u: not u.is_structure
                      and not u.is_flying
                      and u.type_id not in {UnitTypeId.LARVA, UnitTypeId.EGG}
                      and u.distance_to(unit) < reaper_grenade_range
        )
        controller = GridMover(self.ai, unit)
        if smart_action == ACTION_DO_NOTHING:
            return True
        if smart_action == ACTION_MOVE_UP:
            controller.move_up()
            return True
        if smart_action == ACTION_MOVE_DOWN:
            controller.move_down()
            return True
        if smart_action == ACTION_MOVE_LEFT:
            controller.move_left()
            return True
        if smart_action == ACTION_MOVE_RIGHT:
            controller.move_right()
            return True

        if smart_action == ACTION_MOVE_UP_RIGHT:
            controller.move_up_right()
            return True
        if smart_action == ACTION_MOVE_UP_LEFT:
            controller.move_up_left()
            return True
        if smart_action == ACTION_MOVE_DOWN_LEFT:
            controller.move_down_left()
            return True
        if smart_action == ACTION_MOVE_DOWN_RIGHT:
            controller.move_down_right()
            return True
        if smart_action == ACTION_ATTACK_CLOSEST_ENEMY and closest:
            controller.attack(closest)
            return True
        elif not closest:  # no closest in sight
            self.ai.do(unit.move(random.choice(self.ai.enemy_start_locations)))
            return True

        if smart_action == ACTION_ATTACK_WEAKEST_ENEMY and weakest:
            controller.attack(weakest)
            return True
        elif not weakest:  # no weakest in sight
            self.ai.do(unit.move(random.choice(self.ai.enemy_start_locations)))
            return True

        if smart_action == ACTION_ATTACK_THROW_GRENADE and (weakest or closest):
            controller.attack_throw_grenade(weakest, closest)
            return True
        else:  # no weakest in sight
            self.ai.do(unit.move(random.choice(self.ai.enemy_start_locations)))
            return True

    async def execute(self):
        lost_reaper = False
        if not len(self.ai.units(UnitTypeId.REAPER)):
            return True
        for r in self.ai.units(UnitTypeId.REAPER):
            # hack,  if you are safe, and injured  heal up dont look for enemies
            if self.is_safe_ground(r) and r.health_percentage < 0.8:
                continue

            enemies = self.ai.enemy_units | self.ai.enemy_structures
            enemy_close = enemies.filter(lambda unit: unit.can_attack_ground and unit.distance_to(r) < 25)
            if not enemy_close:
                self.policy = Policy.Offensive
                loc = random.choice(self.ai.enemy_start_locations).towards_with_random_angle(
                    self.ai.game_info.map_center, distance=10)
                self.ai.do(r.move(loc))
                continue
            friendlies = self.ai.units.filter(lambda unit: unit.distance_to(r) < 6)
            killed_value_units = self.ai.state.score.killed_value_units
            structures_dmg = self.ai.state.score.killed_value_structures
            damage_dealt = self.ai.state.score.total_damage_dealt_life
            enemies_can_attack = enemies.filter(lambda unit: unit.can_attack_ground)
            if len(self.ai.units(UnitTypeId.REAPER)) < self.reaper_count:
                lost_reaper = True
                self.lost_reapers += (self.reaper_count + len(self.ai.units(UnitTypeId.REAPER)))
                # print(f"Total reapers died :{self.lost_reapers}")
                # print(f"Damage Dealt : {damage_dealt}")
                # print(f"Enemies died :  {killed_value_units}")

            self.reaper_count = len(self.ai.units(UnitTypeId.REAPER))
            enemy_d = {}
            for i in range(5):
                enemy_d[i] = -99, -99
            try:
                closest_5_enemies = enemies_can_attack[:5]
                for i in range(len(closest_5_enemies)):
                    enemy = enemies_can_attack[i]
                    enemy_angle_to_me, enemy_distance_to_me = self.ai.calculate_angle_distance(r.position_tuple,
                                                                                               enemy.position_tuple)
                    enemy_d[i] = enemy.type_id.value, enemy_angle_to_me * enemy_distance_to_me
            except Exception as e:
                pass
                # print("closest closest exception")
                # print(e)

            current_state = np.zeros(40)
            """
            TODO 5 closest enemies :
            TYPE ( worker , queen, is_flying, is_ranged , distance_to_me, angle_to_me
            NUMBER OF NEARBY FRIENDLIES RADIUS 10 ?
            
            
            """
            for i in range(0, 10, 2):
                enemy_idx = int(i/2)
                current_state[i] = enemy_d[enemy_idx][0]
                current_state[i+1] = enemy_d[enemy_idx][1]
            current_state[30] = self.reaper_count
            current_state[31] = self.ai.state.score.killed_minerals_army
            current_state[32] = self.ai.state.score.killed_minerals_economy
            current_state[33] = self.ai.state.score.killed_minerals_technology
            current_state[34] = self.ai.state.score.killed_vespene_army
            current_state[35] = self.ai.state.score.total_damage_taken_life
            current_state[36] = self.ai.state.score.total_healed_life
            current_state[37] = len(friendlies)
            current_state[38] = self.ai.state.score.killed_value_units

            if self.previous_action is not None:
                reward = 0
                if lost_reaper:
                    reward += LOST_REAPER_PENALTY
                if self.last_structures_dmg < structures_dmg:
                    reward += STRUCTUE_KILL_REWARD
                if self.last_killed_value_units < killed_value_units:
                    reward += UNIT_KILL_REWARD
                if self.last_dmg_dealt == damage_dealt:
                    reward += DAMAGE_PENALTY

                self.qlearn.learn(str(self.previous_state), self.previous_action, reward, str(current_state))

            rl_action = self.qlearn.choose_action(str(current_state))
            smart_action = smart_actions[rl_action]
            self.last_dmg_dealt = damage_dealt
            self.previous_state = current_state
            self.previous_action = rl_action

            if self.ai.iteration % 100 == 0:
                try:
                    import pickle
                    qfile = QFILE
                    with open(qfile, "wb") as f:
                        pickle.dump(self.qlearn, f)
                except Exception as e:
                    print(e)
            if self.ai.iteration % 500 == 0:
                print("Saved")
                with open("report.txt", "a") as f:
                    print(f"iteration : {self.ai.iteration}")
                    print(f" {self.lost_reapers} / {damage_dealt} / {killed_value_units}")
                    f.write(f"iteration : {self.ai.iteration}")
                    f.write(f" rd:{self.lost_reapers} / dd:{damage_dealt}, ed:{killed_value_units}\n")

            await self.do_(r, smart_action, enemies_can_attack)
