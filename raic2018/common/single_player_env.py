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


def get_pos3(x):
    return Vec3(x.x, x.y, x.z)


def get_vel3(x):
    return Vec3(x.velocity_x, x.velocity_y, x.velocity_z)


def get_pos2(x):
    return Vec2(x.x, x.z)


def get_vel2(x):
    return Vec2(x.velocity_x, x.velocity_z)


def create_action(arr, ball, robot):
    vel_fwd, vel_right, jump = arr
    jump = jump > 0.75

    fwd_dir = (get_pos2(ball) - get_pos2(robot)).normalized
    right_dir = Vec2(fwd_dir.y, -fwd_dir.x)
    vel = fwd_dir * vel_fwd + right_dir * vel_right

    action = Action()
    action.target_velocity_x = vel.x * const.ROBOT_MAX_GROUND_SPEED
    action.target_velocity_y = (1 if jump else (0 if robot.touch else -1)) * const.ROBOT_MAX_GROUND_SPEED
    action.target_velocity_z = vel.y * const.ROBOT_MAX_GROUND_SPEED
    action.jump_speed = (1 if jump else 0) * const.ROBOT_MAX_JUMP_SPEED
    return action


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
        self.observation_space = spaces.Box(np.ones(41), -np.ones(41), dtype=np.float32)
        self.action_space = spaces.Box(np.ones(3), -np.ones(3), dtype=np.float32)
        self._local_runner = LocalRunnerClient(two_player=False)
        self._game: Game = None
        self._receive_game()
        self._reward_shaper = RewardShaper([
            RewardFactory('bte', 1.0, BallToEnemyReward),
            RewardFactory('vtb', 0.4, VelToBallReward),
            RewardFactory('bvte', 1.0, BallVelToEnemyReward),
        ])

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
        actions = {r.id: create_action(ac, self._game.ball, r) for r, ac in zip(self._game.robots, split_actions)}
        assert len(actions) == len(split_actions)
        return self._local_runner.act(actions)