from raic2018.common.constants import *
from raic2018.common.constants import ARENA as arena
from raic2018.common.vec3 import Vec3


class Dan:
    def __init__(self, distance: float, normal: Vec3):
        self.distance = distance
        self.normal = normal

    def __lt__(self, other):
        return self.distance < other

    def __gt__(self, other):
        return self.distance > other

    def __iter__(self):
        return iter((self.distance, self.normal))


def clamp(x, low, high=None):
    if high is None:
        return x.clamp_length(low)
    else:
        return max(low, min(high, x))


def length(vec):
    return vec.magnitude


def normalize(vec):
    return vec.normalized


def dan_to_plane(point: Vec3, point_on_plane: Vec3, plane_normal: Vec3):
    return  Dan(Vec3.dot(point - point_on_plane, plane_normal), plane_normal)


def dan_to_sphere_inner(point: Vec3, sphere_center: Vec3, sphere_radius: float):
    return Dan(sphere_radius - length(point - sphere_center), normalize(sphere_center - point))


def dan_to_sphere_outer(point: Vec3, sphere_center: Vec3, sphere_radius: float):
    return Dan(length(point - sphere_center) - sphere_radius, normalize(point - sphere_center))


def dan_to_arena_quarter(point: Vec3):
    # Ground
    dan = dan_to_plane(point, Vec3(0, 0, 0), Vec3(0, 1, 0))

    # Ceiling
    dan = min(dan, dan_to_plane(point, Vec3(0, arena.height, 0), Vec3(0, -1, 0)))

    # Side x
    dan = min(dan, dan_to_plane(point, Vec3(arena.width / 2, 0, 0), Vec3(-1, 0, 0)))

    # Side z (goal)
    dan = min(dan, dan_to_plane(
        point,
        Vec3(0, 0, (arena.depth / 2) + arena.goal_depth),
        Vec3(0, 0, -1)))

    # Side z
    v = Vec3(point.x, point.y) - \
        Vec3(arena.goal_width / 2 - arena.goal_top_radius, arena.goal_height - arena.goal_top_radius)
    if point.x >= (arena.goal_width / 2) + arena.goal_side_radius or \
            point.y >= arena.goal_height + arena.goal_side_radius or \
            (v.x > 0 and v.y > 0 and length(v) >= arena.goal_top_radius + arena.goal_side_radius):
        dan = min(dan, dan_to_plane(point, Vec3(0, 0, arena.depth / 2), Vec3(0, 0, -1)))

    # Side x & ceiling (goal)
    if point.z >= (arena.depth / 2) + arena.goal_side_radius:
        # x
        dan = min(dan, dan_to_plane(
            point,
            Vec3(arena.goal_width / 2, 0, 0),
            Vec3(-1, 0, 0)))
        # y
        dan = min(dan, dan_to_plane(point, Vec3(0, arena.goal_height, 0), Vec3(0, -1, 0)))

    # Goal back corners
    assert arena.bottom_radius == arena.goal_top_radius
    if point.z > (arena.depth / 2) + arena.goal_depth - arena.bottom_radius:
        dan = min(dan, dan_to_sphere_inner(
            point,
            Vec3(
                clamp(point.x,
                      arena.bottom_radius - (arena.goal_width / 2),
                      (arena.goal_width / 2) - arena.bottom_radius),
                clamp(point.y,
                      arena.bottom_radius,
                      arena.goal_height - arena.goal_top_radius),
                (arena.depth / 2) + arena.goal_depth - arena.bottom_radius),
            arena.bottom_radius))

    # Corner
    if point.x > (arena.width / 2) - arena.corner_radius and point.z > (arena.depth / 2) - arena.corner_radius:
        dan = min(dan, dan_to_sphere_inner(
            point,
            Vec3((arena.width / 2) - arena.corner_radius,
                 point.y,
                 (arena.depth / 2) - arena.corner_radius),
            arena.corner_radius))

    # Goal outer corner
    if point.z < (arena.depth / 2) + arena.goal_side_radius:
        # Side x
        if point.x < (arena.goal_width / 2) + arena.goal_side_radius:
            dan = min(dan, dan_to_sphere_outer(
                point,
                Vec3(
                    (arena.goal_width / 2) + arena.goal_side_radius,
                    point.y,
                    (arena.depth / 2) + arena.goal_side_radius
                ),
                arena.goal_side_radius))
        # Ceiling
        if point.y < arena.goal_height + arena.goal_side_radius:
            dan = min(dan, dan_to_sphere_outer(
                point,
                Vec3(
                    point.x,
                    arena.goal_height + arena.goal_side_radius,
                    (arena.depth / 2) + arena.goal_side_radius
                ),
                arena.goal_side_radius))
        # Top corner
        o = Vec3(
            (arena.goal_width / 2) - arena.goal_top_radius,
            arena.goal_height - arena.goal_top_radius
        )
        v = Vec3(point.x, point.y) - o
        if v.x > 0 and v.y > 0:
            o = o + normalize(v) * (arena.goal_top_radius + arena.goal_side_radius)
            dan = min(dan, dan_to_sphere_outer(
            point,
                Vec3(o.x, o.y, (arena.depth / 2) + arena.goal_side_radius),
            arena.goal_side_radius))

    # Goal inside top corners
    if point.z > (arena.depth / 2) + arena.goal_side_radius and point.y > arena.goal_height - arena.goal_top_radius:
        # Side x
        if point.x > (arena.goal_width / 2) - arena.goal_top_radius:
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(
                    (arena.goal_width / 2) - arena.goal_top_radius,
                    arena.goal_height - arena.goal_top_radius,
                    point.z
                ),
                arena.goal_top_radius))
        # Side z
        if point.z > (arena.depth / 2) + arena.goal_depth - arena.goal_top_radius:
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(
                    point.x,
                    arena.goal_height - arena.goal_top_radius,
                    (arena.depth / 2) + arena.goal_depth - arena.goal_top_radius
                ),
                arena.goal_top_radius))

    # Bottom corners
    if point.y < arena.bottom_radius:
        # Side x
        if point.x > (arena.width / 2) - arena.bottom_radius:
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(
                    (arena.width / 2) - arena.bottom_radius,
                    arena.bottom_radius,
                    point.z
                ),
                arena.bottom_radius))
        # Side z
        if point.z > (arena.depth / 2) - arena.bottom_radius and point.x >= (arena.goal_width / 2) + arena.goal_side_radius:
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(
                    point.x,
                    arena.bottom_radius,
                    (arena.depth / 2) - arena.bottom_radius
                ),
                arena.bottom_radius))
        # Side z (goal)
        if point.z > (arena.depth / 2) + arena.goal_depth - arena.bottom_radius:
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(
                    point.x,
                    arena.bottom_radius,
                    (arena.depth / 2) + arena.goal_depth - arena.bottom_radius
                ),
                arena.bottom_radius))
        # Goal outer corner
        o = Vec3(
            (arena.goal_width / 2) + arena.goal_side_radius,
            (arena.depth / 2) + arena.goal_side_radius
        )
        v = Vec3(point.x, point.z) - o
        if v.x < 0 and v.y < 0 and length(v) < arena.goal_side_radius + arena.bottom_radius:
            o = o + normalize(v) * (arena.goal_side_radius + arena.bottom_radius)
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(o.x, arena.bottom_radius, o.y),
                arena.bottom_radius))
        # Side x (goal)
        if point.z >= (arena.depth / 2) + arena.goal_side_radius and point.x > (arena.goal_width / 2) - arena.bottom_radius:
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(
                    (arena.goal_width / 2) - arena.bottom_radius,
                    arena.bottom_radius,
                    point.z
                ),
                arena.bottom_radius))
        # Corner
        if point.x > (arena.width / 2) - arena.corner_radius and point.z > (arena.depth / 2) - arena.corner_radius:
            corner_o = Vec3(
                (arena.width / 2) - arena.corner_radius,
                (arena.depth / 2) - arena.corner_radius
            )
            n = Vec3(point.x, point.z) - corner_o
            dist = n.len()
            if dist > arena.corner_radius - arena.bottom_radius:
                n = n / dist
                o2 = corner_o + n * (arena.corner_radius - arena.bottom_radius)
                dan = min(dan, dan_to_sphere_inner(
                    point,
                    Vec3(o2.x, arena.bottom_radius, o2.y),
                    arena.bottom_radius))

    # Ceiling corners
    if point.y > arena.height - arena.top_radius:
        # Side x
        if point.x > (arena.width / 2) - arena.top_radius:
            dan = min(dan, dan_to_sphere_inner(
            point,
            Vec3(
                (arena.width / 2) - arena.top_radius,
                arena.height - arena.top_radius,
                point.z,
            ),
            arena.top_radius))
        # Side z
        if point.z > (arena.depth / 2) - arena.top_radius:
            dan = min(dan, dan_to_sphere_inner(
                point,
                Vec3(
                    point.x,
                    arena.height - arena.top_radius,
                    (arena.depth / 2) - arena.top_radius,
                ),
                arena.top_radius))
        # Corner
        if point.x > (arena.width / 2) - arena.corner_radius and point.z > (arena.depth / 2) - arena.corner_radius:
            corner_o = Vec3(
                (arena.width / 2) - arena.corner_radius,
                (arena.depth / 2) - arena.corner_radius
            )
            dv = Vec3(point.x, point.z) - corner_o
            if length(dv) > arena.corner_radius - arena.top_radius:
                n = normalize(dv)
                o2 = corner_o + n * (arena.corner_radius - arena.top_radius)
                dan = min(dan, dan_to_sphere_inner(
                    point,
                    Vec3(o2.x, arena.height - arena.top_radius, o2.y),
                    arena.top_radius))
    return dan


def dan_to_arena(point: Vec3):
    negate_x = point.x < 0
    negate_z = point.z < 0
    if negate_x:
        point.x = -point.x
    if negate_z:
        point.z = -point.z
    result = dan_to_arena_quarter(point)
    if negate_x:
        result.normal.x = -result.normal.x
    if negate_z:
        result.normal.z = -result.normal.z
    return result