from typing import List, Union, Collection, Iterable

import raic2018.common.constants as const
from raic2018.model import Game, Robot, Ball, Action
from raic2018.common.lr_client import LocalRunnerClient, Winner
import numpy as np
import gym
from gym import spaces
from raic2018.common.vec2 import Vec2
from raic2018.common.vec3 import Vec3
from raic2018.common.reward_shaping import RewardFactory, RewardShaper, KeepCloseToBallReward, BallToEnemyReward, BallVelToEnemyReward, VelToBallReward
from .action_spaces import MultiDiscreteActions


def get_pos_vel(obj: Union[Robot, Ball]) -> Iterable[float]:
    pos = np.array([obj.x, obj.y, obj.z]) * 2 / const.ARENA.depth
    vel = np.array([obj.velocity_x, obj.velocity_y, obj.velocity_z]) / const.ROBOT_MAX_GROUND_SPEED
    return [
        *pos,
        *vel,
        *(vel * 5).clip(-1, 1),
    ]


def game_to_obs(game: Game) -> List[float]:
    ball_pos = np.array([game.ball.x, game.ball.y, game.ball.z])
    obs = []
    obs.extend(get_pos_vel(game.ball))
    for r in game.robots:
        robot_pos = np.array([r.x, r.y, r.z])
        obs.extend((5 * (ball_pos - robot_pos) * 2 / const.ARENA.depth).clip(-1, 1))
        obs.extend(get_pos_vel(r))
        bdir = Vec3(game.ball.x, game.ball.y, game.ball.z) - Vec3(r.x, r.y, r.z)
        obs.extend(bdir / bdir.magnitude)
        obs.append(int(r.touch))
    return obs


class FrameSkipEnv(gym.Wrapper):
    def __init__(self, env, skip=4):
        gym.Wrapper.__init__(self, env)
        self._skip = skip

    def step(self, action):
        total_reward = 0.0
        reward_infos = []
        done = None
        for i in range(self._skip):
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            if 'reward_info' in info:
                reward_infos.append(info['reward_info'])
            if done:
                break

        if len(reward_infos) != 0:
            info['reward_info'] = {k: np.sum([inf[k] for inf in reward_infos]) for k in reward_infos[0].keys()}
        return obs, total_reward, done, info

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)


class HelperFrameSkipEnv(FrameSkipEnv):
    def __init__(self):
        super().__init__(HelperEnv())


class HelperEnv(gym.Env):
    def __init__(self):
        self._actions = MultiDiscreteActions()
        self.observation_space = spaces.Box(np.ones(41), -np.ones(41), dtype=np.float32)
        self._local_runner = LocalRunnerClient(two_player=False)
        self._game: Game = None
        self._receive_game()
        self._reward_shaper = RewardShaper([
            RewardFactory('bte', 1.0, BallToEnemyReward),
            RewardFactory('vtb', 0.4, VelToBallReward),
            RewardFactory('bvte', 1.0, BallVelToEnemyReward),
        ])

    @property
    def action_space(self): return self._actions.space

    def step(self, action: Iterable[float]):
        winner = self._act(action)

        true_reward = 0 if winner is None else (1 if winner == Winner.First else -1)
        self._receive_game()
        state = game_to_obs(self._game)
        aux_rewards = self._reward_shaper.get_rewards(self._game)
        aux_total = np.sum([r.reward for r in aux_rewards])
        aux_info = {f'{r.name}_reward': r.reward for r in aux_rewards}
        info = dict(reward_info=dict(aux_total=aux_total, true_reward=true_reward, **aux_info))
        if winner is not None:
            for _ in range(const.RESET_TICKS + 1):
                self._act(action)
                self._receive_game()
            self._reward_shaper.reset()
        return state, 0.15 * true_reward + aux_total, winner is not None, info

    def reset(self):
        return game_to_obs(self._game)

    def render(self, mode='human'):
        pass

    def _receive_game(self):
        self._game = self._local_runner.get_states()[0]
        self._game.robots.sort(key=lambda r: int(not r.is_teammate) * 1000 + r.id)

    def _act(self, action):
        split_actions = np.split(np.asarray(action), len(self._game.robots) // 2)
        actions = {r.id: self._actions.create_action(ac, r, self._game) for r, ac in zip(self._game.robots, split_actions)}
        assert len(actions) == len(split_actions)
        return self._local_runner.act(actions)