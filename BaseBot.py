import os
import sys

from sc2.unit import Unit

from Sc2botAI.settings import PROJECT_DIR

sys.path.append(os.path.join(os.path.dirname(__file__), PROJECT_DIR))
import numpy as np
import sc2
from sc2.position import Point2, Point3
from Sc2botAI.base.managers.map_manager import MapManager
from Sc2botAI.base.managers.debug_manager import DebugManager
from datetime import datetime as dt
from Sc2botAI.base.drivers.reaper import ReaperDriver
from Sc2botAI.base.drivers.reaper_q import ReaperQAgent

qfile = "reaper_q_driver.pickle"

class BaseBot(sc2.BotAI):

    def __init__(self, debug=False):
        super().__init__()
        ra = ReaperQAgent(ai=self)
        import pickle
        if os.path.exists(qfile):
            with open(qfile, "rb") as f:
                ra = ReaperQAgent(ai=self, qtable=pickle.load(f))
        self.created_at = dt.timestamp(dt.now())
        self.debug = debug
        self.debug_manager = DebugManager(ai=self)
        self.map_manager = MapManager(ai=self)
        self._solved = False
        self.drivers = [ra]
        self.iteration = 0

    async def on_step(self, iteration):
        self.iteration = iteration
        if not self._solved:
            self.map_manager.solve_expansions()
            self._solved = True
        for driver in self.drivers:
            if self.units(driver.condition):
                await driver.execute()
        # debug always last
        if self.debug:
            self.debug_manager.draw_debug()

            async def on_building_construction_started(self, unit: Unit):
                print(f"Construction of building {unit} started at {unit.position}.")

            async def on_building_construction_complete(self, unit: Unit):
                print(f"Construction of building {unit} completed at {unit.position}.")

            async def on_enemy_unit_entered_vision(self, unit: Unit):
                print(f" {unit} entered vision at {unit.position}.")

    def __repr__(self):
        return f'<BaseBot: {str(self.created_at)}>'


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