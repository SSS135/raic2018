from typing import List, Tuple, Callable

import numpy as np
import raic2018.common.constants as const
from raic2018.common.vec2 import Vec2
from raic2018.common.vec3 import Vec3
from raic2018.model import Game
from typing import NamedTuple


class Reward:
    def get_reward(self, game: Game) -> float:
        raise NotImplementedError


class RewardInfo(NamedTuple):
    name: str
    reward: float
    unscaled_reward: float


class RewardFactory(NamedTuple):
    name: str
    scale: float
    factory: Callable[[], Reward]


class RewardShaper:
    def __init__(self, rewards_factories: List[RewardFactory]):
        self.rewards_factories = rewards_factories
        self._reset = True
        self._rewards: List[Reward] = None
        self.reset()

    def get_rewards(self, game: Game) -> List[RewardInfo]:
        if self._reset:
            self._rewards = [f.factory() for f in self.rewards_factories]

        rewards = []
        for f, r in zip(self.rewards_factories, self._rewards):
            r = r.get_reward(game)
            if self._reset:
                r = 0
            rewards.append(RewardInfo(f.name, f.scale * r, r))

        self._reset = False
        return rewards

    def reset(self):
        self._reset = True


class KeepCloseToBallReward(Reward):
    def __init__(self):
        self._prev_reward = -1000

    def get_reward(self, game: Game) -> float:
        ball_pos = Vec2(game.ball.x, game.ball.z)
        mean_dist = np.min([(ball_pos - Vec2(r.x, r.z)).magnitude for r in game.robots if r.is_teammate]).item()
        cur_reward = -mean_dist / const.ARENA.depth
        reward = cur_reward - self._prev_reward
        self._prev_reward = cur_reward
        return reward


class BallToEnemyReward(Reward):
    def __init__(self):
        self._prev_reward = -1000

    def get_reward(self, game: Game) -> float:
        target_pos = Vec3(0, 0, const.ARENA.depth / 2)
        ball_pos = Vec3(game.ball.x, game.ball.y, game.ball.z)
        cur_reward = -(target_pos - ball_pos).magnitude * 2 / const.ARENA.depth
        reward = cur_reward - self._prev_reward
        self._prev_reward = cur_reward
        return reward


class BallVelToEnemyReward(Reward):
    def get_reward(self, game: Game):
        target_pos = Vec3(0, 0, const.ARENA.depth / 2)
        ball_pos = Vec3(game.ball.x, game.ball.y, game.ball.z)
        ball_vel = Vec3(game.ball.velocity_x, game.ball.velocity_y, game.ball.velocity_z)
        target_dir = (target_pos - ball_pos).normalized
        cur_reward = target_dir @ ball_vel / const.MAX_ENTITY_SPEED
        if cur_reward < 0:
            cur_reward *= 0.75
        return 0.015 * cur_reward


class VelToBallReward(Reward):
    def get_reward(self, game: Game):
        ball_pos = Vec3(game.ball.x, game.ball.y, game.ball.z)

        def get_reward(robot):
            robot_pos = Vec3(robot.x, robot.y, robot.z)
            robot_vel = Vec3(robot.velocity_x, robot.velocity_y, robot.velocity_z)
            ball_dir = (ball_pos - robot_pos).normalized
            return max(0, ball_dir @ robot_vel / const.MAX_ENTITY_SPEED)

        cur_reward = np.mean([get_reward(r) for r in game.robots if r.is_teammate])

        return 0.01 * cur_reward