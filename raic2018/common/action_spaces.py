from typing import List, Union, Collection, Iterable

import raic2018.common.constants as const
from raic2018.model import Game, Robot, Ball, Action
import numpy as np
import gym
from gym import spaces
from raic2018.common.vec2 import Vec2
from raic2018.common.vec3 import Vec3


def get_pos3(x):
    return Vec3(x.x, x.y, x.z)


def get_vel3(x):
    return Vec3(x.velocity_x, x.velocity_y, x.velocity_z)


def get_pos2(x):
    return Vec2(x.x, x.z)


def get_vel2(x):
    return Vec2(x.velocity_x, x.velocity_z)


class ActionSpace:
    @property
    def space(self) -> gym.Space:
        raise NotImplementedError

    def create_action(self, action: np.ndarray, robot: Robot, game: Game) -> Action:
        raise NotImplementedError


class ContinuousBallActions(ActionSpace):
    @property
    def space(self):
        return spaces.Box(np.ones(3), -np.ones(3), dtype=np.float32)

    def create_action(self, action: Collection, robot: Robot, game: Game):
        vel_fwd, vel_right, jump = action
        jump = jump > 0.75

        fwd_dir = (get_pos2(game.ball) - get_pos2(robot)).normalized
        right_dir = Vec2(fwd_dir.y, -fwd_dir.x)
        vel = fwd_dir * vel_fwd + right_dir * vel_right

        action = Action()
        action.target_velocity_x = vel.x * const.ROBOT_MAX_GROUND_SPEED
        action.target_velocity_y = (1 if jump else (0 if robot.touch else -1)) * const.ROBOT_MAX_GROUND_SPEED
        action.target_velocity_z = vel.y * const.ROBOT_MAX_GROUND_SPEED
        action.jump_speed = (1 if jump else 0) * const.ROBOT_MAX_JUMP_SPEED
        return action


class ContinuousDoubleActions(ActionSpace):
    @property
    def space(self):
        return spaces.Box(np.ones(5), -np.ones(5), dtype=np.float32)

    def create_action(self, action: Collection, robot: Robot, game: Game):
        vel_fwd, vel_right, jump, vel_x, vel_z = action

        fwd_dir = (get_pos2(game.ball) - get_pos2(robot)).normalized
        right_dir = Vec2(fwd_dir.y, -fwd_dir.x)
        vel = fwd_dir * vel_fwd + right_dir * vel_right
        vel = Vec3(vel.x + vel_x, 0, vel.y + vel_z)

        orig_vel_len = vel.magnitude
        normal = Vec3(robot.touch_normal_x, robot.touch_normal_y, robot.touch_normal_z) \
            if robot.touch_normal_x is not None else Vec3(0, 1, 0)
        vel -= normal * Vec3.dot(normal, vel)
        vel = vel.normalized * orig_vel_len

        action = Action()
        action.target_velocity_x = vel.x * const.ROBOT_MAX_GROUND_SPEED
        action.target_velocity_y = vel.y * const.ROBOT_MAX_GROUND_SPEED
        action.target_velocity_z = vel.z * const.ROBOT_MAX_GROUND_SPEED
        action.jump_speed = (1 if jump > 0.75 else (-1 if jump < -0.75 else 0)) * const.ROBOT_MAX_JUMP_SPEED
        return action


class MultiDiscreteActions(ActionSpace):
    @property
    def space(self):
        # x(+a, -a, +b, -b, 0), z(+a, -a, +b, -b, 0), y(+, -, 0), jump(+, -, 0), nitro(1, 0)
        return spaces.MultiDiscrete([5, 5, 3, 3, 2])

    def create_action(self, action: Collection, robot: Robot, game: Game):
        ac_x, ac_z, ac_y, ac_jump, ac_nitro = action

        fwd_dir = (get_pos2(game.ball) - get_pos2(robot)).normalized
        fwd_dir = Vec3(fwd_dir.x, 0, fwd_dir.y)
        right_dir = Vec3(fwd_dir.z, 0, -fwd_dir.x)

        x_vals = Vec3(1, 0, 0), Vec3(-1, 0, 0), right_dir, -right_dir, Vec3()
        y_vals = Vec3(0, 1, 0), Vec3(0, -1, 0), Vec3()
        z_vals = Vec3(0, 0, 1), Vec3(0, 0, -1), fwd_dir, -fwd_dir, Vec3()
        jump_vals = 1, -1, 0
        nitro_vals = True, False

        vel = x_vals[ac_x] + y_vals[ac_y] + z_vals[ac_z]
        jump = jump_vals[ac_jump]

        orig_vel_len = vel.magnitude
        normal = Vec3(robot.touch_normal_x, robot.touch_normal_y, robot.touch_normal_z) \
            if robot.touch_normal_x is not None else Vec3(0, 1, 0)
        vel -= normal * Vec3.dot(normal, vel)
        vel = vel.normalized * orig_vel_len

        action = Action()
        action.target_velocity_x = vel.x * const.ROBOT_MAX_GROUND_SPEED
        action.target_velocity_y = vel.y * const.ROBOT_MAX_GROUND_SPEED
        action.target_velocity_z = vel.z * const.ROBOT_MAX_GROUND_SPEED
        action.jump_speed = jump * const.ROBOT_MAX_JUMP_SPEED
        action.use_nitro = nitro_vals[ac_nitro]
        return action