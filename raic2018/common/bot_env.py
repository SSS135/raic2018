import random
from typing import List, Tuple

import gym.spaces
import numpy as np

from .detached_mad_cars import DetachedMadCars
from .reward_shaper import RewardShaper, Winner
from .strategy import Strategy
from .types import TickStep
from ..bots.bot0 import Bot0Strategy
from ..bots.bot1 import Bot1Strategy
from ..bots.bot2 import Bot2Strategy
from ..bots.bot3 import Bot3Strategy
from ..bots.bot4 import Bot4Strategy
from ..common.state_processor import StateProcessor, get_space_sizes


def get_spaces(version: int) -> Tuple[gym.Space, gym.Space]:
    obs_len, act_len = get_space_sizes(version)
    observation_space = gym.spaces.Box(low=-1, high=1, shape=(obs_len,), dtype=np.float32)
    action_space = gym.spaces.Discrete(act_len)
    return observation_space, action_space


class MadCarsAIEnv(gym.Env):
    strategies = [Bot0Strategy, Bot1Strategy, Bot2Strategy, Bot3Strategy, Bot4Strategy]

    def __init__(self, version=2):
        self.version = version
        self.game = DetachedMadCars()
        self.proc: StateProcessor = None
        self.internal_bot_index: int = None
        self.player_index: int = None
        self.bot: Strategy = None
        self.ticks: List[TickStep] = None
        self.state: np.ndarray = None
        self.reward_shaper: RewardShaper = None
        self.observation_space, self.action_space = get_spaces(version)

    def reset(self) -> np.ndarray:
        self.ticks = self.game.reset()
        self.internal_bot_index = random.randrange(2)
        self.player_index = (self.internal_bot_index + 1) % 2
        self.proc = StateProcessor(self.game.game_infos[self.player_index], self.version)
        self.reward_shaper = RewardShaper(self.game.game_infos[self.player_index])
        self.bot = self._get_bot()
        self.bot.process_data(self.game.game_infos[self.internal_bot_index])
        self.state = None
        return self.proc.update_state(self.ticks[self.player_index])

    def step(self, action: int) -> (np.ndarray, float, bool, dict):
        while True:
            player_cmd = self.proc.get_command(action)
            bot_cmd = self.bot.process_data(self.ticks[self.internal_bot_index])['command']
            commands = [player_cmd, bot_cmd]
            if self.player_index == 1:
                commands.reverse()
            self.ticks, winner_id, done = self.game.step(commands)
            reward, reward_info = self._get_reward(winner_id, done)
            if done:
                return self.state, reward, done, reward_info
            new_state = self.proc.update_state(self.ticks[self.player_index])
            if new_state is not None:
                self.state = new_state
                return self.state, reward, done, reward_info

    def render(self, mode='human'):
        pass

    def _get_bot(self) -> Strategy:
        strategy = random.choice(self.strategies)
        return strategy()

    def _get_reward(self, winner_id: int, done: bool) -> float:
        if winner_id == -1:
            winner = Winner.No
        else:
            winner = Winner.Self if winner_id == self.player_index else Winner.Enemy
        tick = self.ticks[self.player_index]
        return self.reward_shaper.get_reward(tick, winner, done)
