import random
from itertools import count
from typing import List

import numpy as np
from common.reward_shaper import RewardShaper, Winner
from ppo_pytorch.common.multiplayer_env import MultiplayerEnv

from .bot_env import get_spaces
from .detached_mad_cars import DetachedMadCars
from .types import NewMatchStep, TickStep
from ..common.state_processor import StateProcessor


class PlayerProcessor:
    def __init__(self, game_info: NewMatchStep, version):
        self.proc: StateProcessor = None
        self.prev_aux_reward: float = None
        self.ticks: List[TickStep] = None
        self.proc = StateProcessor(game_info, version)
        self.reward_shaper = RewardShaper(game_info)

    def get_command(self, index, rand_state) -> str:
        random.setstate(rand_state)
        return self.proc.get_command(index)

    def step(self, tick: TickStep, winner: Winner, done: bool, rand_state) -> (np.ndarray, float, dict):
        random.setstate(rand_state)
        reward, reward_info = self.reward_shaper.get_reward(tick, winner, done)
        if done:
            return None, reward, reward_info
        state = self.proc.update_state(tick)
        return state, reward, reward_info


class MadCarsMultiplayerEnv(MultiplayerEnv):
    def __init__(self, version=2):
        super().__init__(num_players=2)
        self.version = version
        self.game = DetachedMadCars()
        self.processors: List[PlayerProcessor] = None
        self.states = None
        self.observation_space, self.action_space = get_spaces(self.version)

    def reset(self) -> np.ndarray:
        ticks = self.game.reset()
        rand_state = random.getstate()
        self.processors = [PlayerProcessor(inf, self.version) for inf in self.game.game_infos]
        self.states, _, _ = zip(*[p.step(t, False, False, rand_state) for (p, t) in zip(self.processors, ticks)])
        self.states = np.array(self.states)
        return self.states

    def step(self, actions: List[int]) -> (np.ndarray, np.ndarray, bool, List[dict]):
        while True:
            rand_state = random.getstate()
            commands = [p.get_command(a, rand_state) for (p, a) in zip(self.processors, actions)]
            ticks, winner_id, done = self.game.step(commands)
            rand_state = random.getstate()
            new_states, rewards, reward_infos = zip(*[p.step(t, self._get_win_status(i, winner_id), done, rand_state)
                                                      for (i, p, t) in zip(count(), self.processors, ticks)])
            assert sum(s is None for s in new_states) in (0, len(new_states))
            if new_states[0] is not None:
                self.states = np.array(new_states)
            if done or new_states[0] is not None:
                return self.states, np.array(rewards), done, reward_infos

    def _get_win_status(self, id: int, winner_id: int) -> Winner:
        if winner_id == -1:
            return Winner.No
        else:
            return Winner.Self if winner_id == id else Winner.Enemy

    def render(self, mode='human'):
        pass
