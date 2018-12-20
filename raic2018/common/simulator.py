from typing import List, Optional

from raic2018.common.constants import *
from raic2018.common.vec3 import Vec3
from raic2018.common.simulator_collision import length, normalize, clamp, dan_to_arena
import random
import copy


class Entity:
    def __init__(self, pos: Vec3, vel: Vec3, radius: float, mass: float, radius_change_speed: float, arena_e: float):
        self.position = pos
        self.velocity = vel
        self.radius = radius
        self.mass = mass
        self.radius_change_speed = radius_change_speed
        self.arena_e = arena_e


class Action:
    def __init__(self, target_velocity: Vec3, jump_speed: float, use_nitro: bool):
        self.target_velocity = target_velocity
        self.use_nitro = use_nitro
        self.jump_speed = jump_speed


class Robot(Entity):
    def __init__(self, nitro: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action = Action(Vec3.zero, 0, False)
        self.touch = True
        self.touch_normal = Vec3(0, 1, 0)
        self.nitro = nitro


class NitroPack(Entity):
    def __init__(self, respawn_ticks: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.respawn_ticks = respawn_ticks


def create_sim(num_robots: int, nitro: bool):
    assert not nitro

    ball_pos = Vec3(0, BALL_RADIUS * random.uniform(1, 4), 0)
    ball = Entity(ball_pos, Vec3.zero, BALL_RADIUS, BALL_MASS, 0, BALL_ARENA_E)

    start_nitro = START_NITRO_AMOUNT if nitro else 0
    robots = []
    for _ in range(num_robots):
        robot_pos = Vec3(
            (ARENA.width / 2 - ARENA.corner_radius) * random.uniform(-1, 1),
            0,
            (ARENA.depth / 2 - ARENA.corner_radius) * random.uniform(0, 1))
        robots.append(Robot(start_nitro, robot_pos, Vec3.zero, ROBOT_RADIUS, ROBOT_MASS, 0, ROBOT_ARENA_E))
    robots.extend(copy.deepcopy(robots))

    return Simulator(robots, ball, [])


class Simulator:
    def __init__(self, robots: List[Robot], ball: Entity, nitro_packs: List[NitroPack]):
        self.robots = robots
        self.ball = ball
        self.nitro_packs = nitro_packs
        self.winner: Optional[int] = None

    def collide_entities(self, a: Entity, b: Entity):
        delta_position = b.position - a.position
        distance = delta_position.magnitude
        penetration = a.radius + b.radius - distance
        if penetration > 0:
            k_a = (1 / a.mass) / ((1 / a.mass) + (1 / b.mass))
            k_b = (1 / b.mass) / ((1 / a.mass) + (1 / b.mass))
            normal = delta_position.normalized
            a.position -= normal * penetration * k_a
            b.position += normal * penetration * k_b
            delta_velocity = Vec3.dot(b.velocity - a.velocity, normal) + b.radius_change_speed - a.radius_change_speed
            if delta_velocity < 0:
                impulse = (1 + random.uniform(MIN_HIT_E, MAX_HIT_E)) * delta_velocity * normal
                a.velocity += impulse * k_a
                b.velocity -= impulse * k_b

    def collide_with_arena(self, e: Entity):
        distance, normal = dan_to_arena(e.position)
        penetration = e.radius - distance
        if penetration > 0:
            e.position += penetration * normal
            velocity = Vec3.dot(e.velocity, normal) - e.radius_change_speed
            if velocity < 0:
                e.velocity -= (1 + e.arena_e) * velocity * normal
                return normal
        return None

    def move(self, e: Entity, delta_time: float):
        e.velocity = e.velocity.clamp_length(MAX_ENTITY_SPEED)
        e.position += e.velocity * delta_time
        e.position.y -= GRAVITY * delta_time * delta_time / 2
        e.velocity.y -= GRAVITY * delta_time

    def update(self, delta_time: float):
        random.shuffle(self.robots)

        for robot in self.robots:
            if robot.touch:
                target_velocity = robot.action.target_velocity.clamp_length(ROBOT_MAX_GROUND_SPEED)
                target_velocity -= robot.touch_normal * Vec3.dot(robot.touch_normal, target_velocity)
                target_velocity_change = target_velocity - robot.velocity
                if target_velocity_change.magnitude > 0:
                    acceleration = ROBOT_ACCELERATION * max(0, robot.touch_normal.y)
                    robot.velocity += clamp(
                        normalize(target_velocity_change) * acceleration * delta_time,
                        length(target_velocity_change))

            if robot.action.use_nitro:
                target_velocity_change = clamp(
                    robot.action.target_velocity - robot.velocity,
                    robot.nitro * NITRO_POINT_VELOCITY_CHANGE)
                if length(target_velocity_change) > 0:
                    acceleration = normalize(target_velocity_change) * ROBOT_NITRO_ACCELERATION
                    velocity_change = clamp(
                        acceleration * delta_time,
                        length(target_velocity_change))
                    robot.velocity += velocity_change
                    robot.nitro -= length(velocity_change) / NITRO_POINT_VELOCITY_CHANGE
            self.move(robot, delta_time)
            robot.radius = ROBOT_MIN_RADIUS + (ROBOT_MAX_RADIUS - ROBOT_MIN_RADIUS) * robot.action.jump_speed / ROBOT_MAX_JUMP_SPEED
            robot.radius_change_speed = robot.action.jump_speed

        self.move(self.ball, delta_time)

        for i in range(len(self.robots)):
            for j in range(i):
                self.collide_entities(self.robots[i], self.robots[j])

        for robot in self.robots:
            self.collide_entities(robot, self.ball)
            collision_normal = self.collide_with_arena(robot)
            if collision_normal is None:
                robot.touch = False
            else:
                robot.touch = True
                robot.touch_normal = collision_normal

                self.collide_with_arena(self.ball)

        if abs(self.ball.position.z) > ARENA.depth / 2 + self.ball.radius:
            self.goal_scored()

        for robot in self.robots:
            if robot.nitro == MAX_NITRO_AMOUNT:
                continue
            for pack in self.nitro_packs:
                if not pack.alive:
                    continue
                if length(robot.position - pack.position) <= robot.radius + pack.radius:
                    robot.nitro = MAX_NITRO_AMOUNT
                    pack.alive = False
                    pack.respawn_ticks = NITRO_PACK_RESPAWN_TICKS

    def goal_scored(self):
        self.winner = 0 if self.ball.position.z > 0 else 1

    def tick(self):
        assert self.winner is None

        delta_time = 1 / TICKS_PER_SECOND
        for _ in range(MICROTICKS_PER_TICK):
            self. update(delta_time / MICROTICKS_PER_TICK)

        for pack in self.nitro_packs:
            if pack.alive:
                continue
            pack.respawn_ticks -= 1
            if pack.respawn_ticks == 0:
                pack.alive = True