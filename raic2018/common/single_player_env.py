from typing import List, Union, Collection, Iterable

from raic2018.common.constants import ROBOT_MAX_GROUND_SPEED, ROBOT_MAX_JUMP_SPEED, ARENA
from raic2018.model import Game, Robot, Ball, Action
from raic2018.common.lr_client import LocalRunnerClient, Winner
import numpy as np
import gym
from gym import spaces
from raic2018.common.vec2 import Vec2


def get_pos_vel(obj: Union[Robot, Ball]) -> Iterable[float]:
    return [
        obj.x * 2 / ARENA.width,
        obj.y * 2 / ARENA.height,
        obj.z * 2 / ARENA.depth,
        obj.velocity_x / ROBOT_MAX_GROUND_SPEED,
        obj.velocity_y / ROBOT_MAX_GROUND_SPEED,
        obj.velocity_z / ROBOT_MAX_GROUND_SPEED
    ]


def game_to_obs(game: Game) -> List[float]:
    obs = []
    obs.extend(get_pos_vel(game.ball))
    for r in game.robots:
        obs.extend(get_pos_vel(r))
    return obs


def create_action(arr, robot):
    # target = Vec2(arr[0] * ARENA.width / 2, arr[1] * (ARENA.depth + ARENA.goal_depth) / 2)
    # cur = Vec2(robot.x, robot.z)
    # dir = target - cur
    # dir /= dir.magnitude

    vel_x, vel_z = arr

    action = Action()
    action.target_velocity_x = vel_x * ROBOT_MAX_GROUND_SPEED
    # action.target_velocity_y = vel_y * ROBOT_MAX_GROUND_SPEED
    action.target_velocity_z = vel_z * ROBOT_MAX_GROUND_SPEED
    # action.jump_speed = jump * ROBOT_MAX_JUMP_SPEED
    return action


class FrameSkipEnv(gym.Wrapper):
    def __init__(self, env, skip=8):
        gym.Wrapper.__init__(self, env)
        self._skip = skip

    def step(self, action):
        total_reward = 0.0
        done = None
        for i in range(self._skip):
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            if done:
                break

        return obs, total_reward, done, info

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)


class HelperFrameSkipEnv(FrameSkipEnv):
    def __init__(self):
        super().__init__(HelperEnv())


class HelperEnv(gym.Env):
    def __init__(self):
        self.observation_space = spaces.Box(np.ones(30), -np.ones(30), dtype=np.float32)
        self.action_space = spaces.Box(np.ones(4), -np.ones(4), dtype=np.float32)
        self._local_runner = LocalRunnerClient(two_player=False)
        self._game: Game = None
        self._receive_game()
        self._prev_ball_reward = 0

    def step(self, action: Iterable[float]):
        teammate_ids = [r.id for r in self._game.robots if r.is_teammate]
        split_actions = np.split(np.asarray(action), len(teammate_ids))
        actions = {id: create_action(arr, [r for r in self._game.robots if r.is_teammate and r.id == id][0]) for id, arr in zip(teammate_ids, split_actions)}
        winner = self._local_runner.act(actions)
        reward = 0 if winner is None else (1 if winner == Winner.First else -1)
        self._receive_game()
        state = game_to_obs(self._game)
        return state, reward, reward != 0, {}

    def reset(self):
        return game_to_obs(self._game)

    def render(self, mode='human'):
        pass

    def _receive_game(self):
        self._game, = self._local_runner.get_states()
        self._game.robots.sort(key=lambda r: int(not r.is_teammate) * 1000 + r.z)