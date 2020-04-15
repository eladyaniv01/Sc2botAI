import random
from collections import deque

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
from Sc2botAI.settings import QFILE

LOST_REAPER_PENALTY = -12
STRUCTUE_KILL_REWARD = 12
UNIT_KILL_REWARD = 8
DAMAGE_REWARD = 0
DAMAGE_PENALTY = -0.1


# TODO generic training map with adjustable configuration (ie spawn units in middle,  spawn structures,  rules)
# TODO move qlearning table to a generic place for others qagents to import from
# Stolen from https://github.com/MorvanZhou/Reinforcement-learning-with-tensorflow


class PrioritizedReplayBuffer:
    def __init__(self, maxlen):
        self.buffer = deque(maxlen=maxlen)
        self.priorities = deque(maxlen=maxlen)

    def add(self, experience):
        self.buffer.append(experience)
        self.priorities.append(max(self.priorities, default=1))

    def get_probabilities(self, priority_scale):
        scaled_priorities = np.array(self.priorities) ** priority_scale
        sample_probabilities = scaled_priorities / sum(scaled_priorities)
        return sample_probabilities

    def get_importance(self, probabilities):
        importance = 1 / len(self.buffer) * 1 / probabilities
        importance_normalized = importance / max(importance)
        return importance_normalized

    def sample(self, batch_size, priority_scale=1.0):
        sample_size = min(len(self.buffer), batch_size)
        sample_probs = self.get_probabilities(priority_scale)
        sample_indices = random.choices(
            range(len(self.buffer)), k=sample_size, weights=sample_probs
        )
        samples = np.array(self.buffer)[sample_indices]
        importance = self.get_importance(sample_probs[sample_indices])
        return map(list, zip(*samples)), importance, sample_indices

    def set_priorities(self, indices, errors, offset=0.1):
        for i, e in zip(indices, errors):
            self.priorities[i] = abs(e) + offset


class QLearningTable:
    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actions = actions  # a list
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        self.replay_buffer = PrioritizedReplayBuffer(maxlen=100000)

    def choose_action(self, observation):
        self.check_state_exist(observation)
        # action selection
        if np.random.uniform() < self.epsilon:
            # choose best action
            state_action = self.q_table.loc[observation, :]
            # some actions may have the same value, randomly choose on in these actions
            action = np.random.choice(state_action[state_action == np.max(state_action)].index)
            # if self.epsilon > 0.3:
            #     self.epsilon *= self.epsilon
        else:
            # choose random action
            action = np.random.choice(self.actions)
        return action

    def learn(self, state, action, reward, next_state):
        # self.replay_buffer.add((state, action, next_state, reward))
        # (states, actions, next_states, rewards), importance, indices = self.replay_buffer.sample(50, priority_scale=0.0)
        # next_actions = np.argmax(self.choose_action([self.q_table.loc[state, action] for state in states]))
        # q_next_states = [self.q_table.loc[state, action] for state in states]
        # q_next_states_next_actions = q_next_states[np.arange(next_actions.shape[0]), next_actions]
        # q_targets = rewards + self.gamma * q_next_states_next_actions
        # errors = self.q_network.update_model(self.sess, states, actions, q_targets, importance ** (1 - self.eps))
        #
        # self.replay_buffer.set_priorities(indices, errors)
        self.check_state_exist(next_state)
        q_predict = self.q_table.loc[state, action]
        if next_state != "terminal":
            q_target = (
                reward + self.gamma * self.q_table.loc[next_state, :].max()
            )  # next state is not terminal
        else:
            q_target = reward  # next state is terminal
        self.q_table.loc[state, action] += self.lr * (q_target - q_predict)  # update

    def check_state_exist(self, state):
        if state not in self.q_table.index:
            # append new state to q table
            self.q_table = self.q_table.append(
                pd.Series([0] * len(self.actions), index=self.q_table.columns, name=state,)
            )


class Policy(enum.Enum):
    Passive = (0,)
    Offensive = (1,)


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
            # self.ai.do(self.unit.move(random.choice(self.ai.enemy_start_locations)))
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


ACTION_DO_NOTHING = "donothing"
ACTION_MOVE_UP = "moveup"
ACTION_MOVE_DOWN = "movedown"
ACTION_MOVE_LEFT = "moveleft"
ACTION_MOVE_RIGHT = "moveright"
ACTION_MOVE_UP_RIGHT = "moveupright"
ACTION_MOVE_UP_LEFT = "moveupleft"
ACTION_MOVE_DOWN_LEFT = "movedownleft"
ACTION_MOVE_DOWN_RIGHT = "movedownright"
ACTION_ATTACK_CLOSEST_ENEMY = "attackclosestenemy"
ACTION_ATTACK_WEAKEST_ENEMY = "attackweakestenemy"
ACTION_ATTACK_THROW_GRENADE = "attackthrowgrenadeclosestenemy"

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
        self.qlearn.epsilon = 0.9  # start session with 0.9 randomness
        self.unit = unit
        self.distance_to_main = -99
        self.condition = UnitTypeId.REAPER
        self.last_height = -99
        self.is_climbing = 0
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
        self.iteration_state = 0

    async def do_(self, unit, smart_action, enemies_can_attack=None):
        closest = enemies_can_attack.sorted(lambda x: x.distance_to(unit))
        weakest = enemies_can_attack.sorted(lambda x: x.health)
        reaper_grenade_range = self.ai._game_data.abilities[
            AbilityId.KD8CHARGE_KD8CHARGE.value
        ]._proto.cast_range
        enemy_ground_units_in_grenade_range = enemies_can_attack.filter(
            lambda u: not u.is_structure
            and not u.is_flying
            and u.type_id not in {UnitTypeId.LARVA, UnitTypeId.EGG}
            and u.distance_to(unit) < reaper_grenade_range
        )
        closest_grenade = enemy_ground_units_in_grenade_range.sorted(lambda x: x.distance_to(unit))
        weakest_grenade = enemy_ground_units_in_grenade_range.sorted(lambda x: x.health)

        controller = GridMover(self.ai, unit)
        if len(enemies_can_attack) == 0:

            try:
                loc = random.choice(self.ai.enemy_start_locations).towards_with_random_angle(
                    self.ai.game_info.map_center, distance=10
                )
                self.ai.do(unit.move(loc))
            except:
                loc = random.choice(
                    list(self.ai.expansion_locations.keys())
                ).towards_with_random_angle(self.ai.game_info.map_center, distance=10)
                self.ai.do(unit.move(loc))
            return True
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
            # self.ai.do(unit.move(random.choice(self.ai.enemy_start_locations)))
            return True
        if smart_action == ACTION_ATTACK_WEAKEST_ENEMY and weakest:
            controller.attack(weakest)
            return True
        if smart_action == ACTION_ATTACK_THROW_GRENADE and (closest_grenade or weakest_grenade):
            # cant train grenades atm on this map
            # controller.attack_throw_grenade(weakest, closest)
            if closest_grenade:
                controller.attack(closest_grenade)
            else:
                controller.attack(weakest_grenade)
            return True

    async def execute(self, target=None):
        self.qlearn.lr = 0.05
        self.qlearn.epsilon = 0.9
        # if not target:
        # target = random.choice(list(self.ai.expansion_locations.keys()))
        lost_reaper = False
        if not len(self.ai.units(UnitTypeId.REAPER)):

            return True
        self.iteration_state = 0  # 0 started 1 dont do more

        for r in self.ai.units(UnitTypeId.REAPER):
            if self.iteration_state == 0:
                await self.ai.client.move_camera(r.position)
                self.iteration_state = 1
            from threading import Lock

            lock = Lock()
            # hack,  if you are safe, and injured  heal up dont look for enemies
            if self.is_safe_ground(r) and r.health_percentage < 0.8:
                continue
            height = self.ai.get_terrain_z_height(r.position)
            # distance_to_enemy_main = r.position.distance_to(self.ai.enemy_start_locations[0])
            if height > self.last_height:
                self.is_climbing = 1
                self.last_height = height
            else:
                self.is_climbing = 0

            # closest_ramp = self.ai._game_data.map_ramps.
            # r.po
            enemies = self.ai.enemy_units | self.ai.enemy_structures
            enemy_close = enemies.filter(
                lambda unit: unit.can_attack_ground and unit.distance_to(r) < 25
            )
            # if not enemy_close:
            #     self.policy = Policy.Offensive
            #     loc = random.choice(self.ai.enemy_start_locations).towards_with_random_angle(
            #         self.ai.game_info.map_center, distance=10)
            #     self.ai.do(r.move(loc))
            #     continue

            friendlies = self.ai.units.filter(lambda unit: unit.distance_to(r) < 6)
            killed_value_units = self.ai.state.score.killed_value_units
            structures_dmg = self.ai.state.score.killed_value_structures
            damage_dealt = (
                self.ai.state.score.total_damage_dealt_life
                + self.ai.state.score.total_damage_dealt_shields
            )
            enemies_can_attack = enemies.filter(lambda unit: unit.can_attack_ground)
            lost_reapers = (
                self.ai.state.score.lost_minerals_army + self.ai.state.score.lost_vespene_army
            )
            if self.lost_reapers < lost_reapers:
                self.lost_reapers = lost_reapers
                lost_reaper = True

            self.reaper_count = len(self.ai.units(UnitTypeId.REAPER))
            enemy_d = {}
            closest_enemy_distance = -99
            for i in range(5):
                enemy_d[i] = -99, -99, -99
            try:
                closest_5_enemies = enemies_can_attack[:5]
                for i in range(len(closest_5_enemies)):

                    enemy = enemies_can_attack[i]
                    (enemy_angle_to_me, enemy_distance_to_me,) = self.ai.calculate_angle_distance(
                        r.position_tuple, enemy.position_tuple
                    )
                    enemy_d[i] = (
                        enemy.type_id.value,
                        enemy_angle_to_me * enemy_distance_to_me,
                        enemy.health_percentage,
                    )
                    if i == 0:
                        closest_enemy_distance = enemy_distance_to_me
            except Exception as e:
                pass
                # print("closest closest exception")
                # print(e)

            current_state = np.zeros(50)
            # 46 , 47 , 41
            # 45 , p  , 40
            # 43 , 44 , 42
            idx = 40
            for i, pos in enumerate(r.position.neighbors8):
                # print(pos)
                # print(type(pos))
                current_state[idx + i] = self.ai.game_info.pathing_grid[pos.rounded]

            """
            TODO 5 closest enemies :
            TYPE ( worker , queen, is_flying, is_ranged , distance_to_me, angle_to_me
            NUMBER OF NEARBY FRIENDLIES RADIUS 10 ?
            NEIGHBORES 8 PATHABLE CHECKS
            
            """

            for i in range(0, 15, 3):
                enemy_idx = int(i / 3)
                current_state[i] = enemy_d[enemy_idx][0]  # unit id
                current_state[i + 1] = enemy_d[enemy_idx][1]  # distance * angle
                current_state[i + 2] = enemy_d[enemy_idx][2]  # health percent
            current_state[30] = r.health_percentage
            current_state[31] = self.is_climbing
            current_state[32] = self.last_height
            current_state[33] = closest_enemy_distance

            reward = 0
            if self.previous_action is not None:
                if self.last_structures_dmg < structures_dmg:
                    reward += STRUCTUE_KILL_REWARD
                if self.last_killed_value_units < killed_value_units:
                    reward += UNIT_KILL_REWARD
                if lost_reaper:
                    reward += LOST_REAPER_PENALTY
                if (
                    closest_enemy_distance != -99
                    and 7 > closest_enemy_distance
                    and self.last_dmg_dealt <= damage_dealt
                ):
                    reward += closest_enemy_distance
                    reward += (r.health_percentage) * 10
                    # print(reward)
                # if self.distance_to_main > distance_to_enemy_main > 10:
                #     reward += RUN_ENEMY_MAIN_REWARD
                # else:
                #     reward += RUN_ENEMY_MAIN_PENALTY
                # self.distance_to_main = distance_to_enemy_main

                # with lock:
                self.qlearn.learn(
                    str(self.previous_state), self.previous_action, reward, str(current_state),
                )
            # with lock:
            rl_action = self.qlearn.choose_action(str(current_state))
            smart_action = smart_actions[rl_action]
            self.last_dmg_dealt = damage_dealt
            self.previous_state = current_state
            self.previous_action = rl_action

            if lost_reapers == 0:
                lost_reapers = 1

            print(
                f"\riteration : {self.ai.iteration}, Score : {(killed_value_units / lost_reapers):.2f},"
                f" Reward: {reward:.2f}, lost_reapers {lost_reapers},"
                f" killed_value_units : {killed_value_units}, damage_dealt : {damage_dealt}",
                end="",
            )

            if (
                self.ai.iteration % 200 == 0
                or self.ai.iteration % 199 == 0
                or self.ai.iteration % 198 == 0
                and self.iteration_state == 0
            ):
                self.iteration_state = 1
                try:
                    import pickle
                    from threading import Lock

                    # with Lock():
                    qfile = QFILE
                    with open(qfile, "wb") as f:
                        pickle.dump(self.qlearn, f)
                except Exception as e:
                    print(e)

                if (
                    self.ai.iteration % 500 == 0
                    or self.ai.iteration % 499 == 0
                    or self.ai.iteration % 498 == 0
                ):
                    import pickle
                    from threading import Lock

                    with Lock():
                        qfile = "backup.pickle"
                        with open(qfile, "wb") as f:
                            pickle.dump(self.qlearn, f)
                    with open("report.txt", "a") as f:
                        # f.write(f"iteration : {self.ai.iteration}")
                        f.write(f"{killed_value_units/lost_reapers},")
            # self.ai.state.score.lost_minerals_army
            # with lock:
            await self.do_(r, smart_action, enemies_can_attack)
