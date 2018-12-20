from typing import List, Union, Collection, Iterable

import raic2018.common.constants as const
from raic2018.model import Game, Robot, Ball, Action
from raic2018.common.lr_client import LocalRunnerClient, Winner
import numpy as np
import gym
from gym import spaces
from raic2018.common.vec2 import Vec2
from raic2018.common.vec3 import Vec3


def get_pos_vel(obj: Union[Robot, Ball]) -> Iterable[float]:
    return [
        obj.x * 2 / const.ARENA.width,
        obj.y * 2 / const.ARENA.height,
        obj.z * 2 / const.ARENA.depth,
        obj.velocity_x / const.ROBOT_MAX_GROUND_SPEED,
        obj.velocity_y / const.ROBOT_MAX_GROUND_SPEED,
        obj.velocity_z / const.ROBOT_MAX_GROUND_SPEED
    ]


def game_to_obs(game: Game) -> List[float]:
    obs = []
    obs.extend(get_pos_vel(game.ball))
    for r in game.robots:
        obs.extend(get_pos_vel(r))
        bdir = Vec2(game.ball.x, game.ball.z) - Vec2(r.x, r.z)
        obs.extend(bdir / bdir.magnitude)
    return obs


def create_action(arr):
    # target = Vec2(arr[0] * ARENA.width / 2, arr[1] * (ARENA.depth + ARENA.goal_depth) / 2)
    # cur = Vec2(robot.x, robot.z)
    # dir = target - cur
    # dir /= dir.magnitude

    vel_x, vel_y, vel_z, jump = arr

    action = Action()
    action.target_velocity_x = vel_x * const.ROBOT_MAX_GROUND_SPEED
    action.target_velocity_y = vel_y * const.ROBOT_MAX_GROUND_SPEED
    action.target_velocity_z = vel_z * const.ROBOT_MAX_GROUND_SPEED
    action.jump_speed = jump * const.ROBOT_MAX_JUMP_SPEED
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


class RewardBase:
    def __init__(self, scale: float):
        self.scale = scale
        self._do_reset = True

    def get_reward(self, game: Game) -> float:
        raise NotImplementedError

    def reset(self):
        self._do_reset = True


class KeepCloseToBallReward(RewardBase):
    def __init__(self, scale):
        super().__init__(scale)
        self._prev_reward = 0

    def get_reward(self, game: Game) -> float:
        if self._do_reset:
            self._prev_reward = -1000

        ball_pos = Vec2(game.ball.x, game.ball.z)
        min_dist = np.min([(ball_pos - Vec2(r.x, r.z)).magnitude for r in game.robots if r.is_teammate]).item()
        min_dist = min_dist
        cur_reward = -min_dist / const.ARENA.depth
        reward = cur_reward - self._prev_reward
        self._prev_reward = cur_reward

        if self._do_reset:
            self._do_reset = False
            return 0
        return self.scale * reward


class BallToEnemyReward(RewardBase):
    def __init__(self, scale):
        super().__init__(scale)
        self._prev_reward = 0

    def get_reward(self, game: Game) -> float:
        if self._do_reset:
            self._prev_reward = -1000

        target_pos = Vec3(0, 0, const.ARENA.depth / 2)
        ball_pos = Vec3(game.ball.x, game.ball.y, game.ball.z)
        cur_reward = -(target_pos - ball_pos).magnitude * 2 / const.ARENA.depth
        reward = cur_reward - self._prev_reward
        self._prev_reward = cur_reward

        if self._do_reset:
            self._do_reset = False
            return 0
        return self.scale * reward


class HelperEnv(gym.Env):
    def __init__(self):
        self.observation_space = spaces.Box(np.ones(22), -np.ones(22), dtype=np.float32)
        self.action_space = spaces.Box(np.ones(4), -np.ones(4), dtype=np.float32)
        self._local_runner = LocalRunnerClient(two_player=False)
        self._game: Game = None
        self._receive_game()
        self._kctb_reward = KeepCloseToBallReward(1.0)
        self._bte_reward = BallToEnemyReward(1.0)

    def step(self, action: Iterable[float]):
        winner = self._act(action)
        game_ended = winner is not None
        true_reward = 0 if winner is None else (1 if winner == Winner.First else -1)

        self._receive_game()
        state = game_to_obs(self._game)

        bte_reward = self._bte_reward.get_reward(self._game)
        cctb_reward = self._kctb_reward.get_reward(self._game)
        aux_total = bte_reward + cctb_reward
        info = dict(reward_info=dict(aux_total=aux_total, bte_reward=bte_reward, cctb_reward=cctb_reward, true_reward=true_reward))

        if game_ended:
            for _ in range(const.RESET_TICKS + 1):
                self._act(action)
                self._receive_game()
            self._bte_reward.reset()
            self._kctb_reward.reset()

        return state, 0.0 * true_reward + aux_total, game_ended, info

    def reset(self):
        return game_to_obs(self._game)

    def render(self, mode='human'):
        pass

    def _receive_game(self):
        self._game = self._local_runner.get_states()[0]
        self._game.robots.sort(key=lambda r: int(not r.is_teammate) * 1000 + r.id)

    def _act(self, action):
        split_actions = np.split(np.asarray(action), len(self._game.robots) // 2)
        actions = {r.id: create_action(ac) for r, ac in zip(self._game.robots, split_actions)}
        assert len(actions) == len(split_actions)
        return self._local_runner.act(actions)