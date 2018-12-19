# def dan_to_plane(point: Vec3D, point_on_plane: Vec3D, plane_normal: Vec3D):
#     return  distance: dot(point - point_on_plane, plane_normal), normal: plane_normal
#
# def dan_to_sphere_inner(point: Vec3D, sphere_center: Vec3D, sphere_radius: Float):
#     return distance: sphere_radius - length(point - sphere_center), normal: normalize(sphere_center - point)
#
# def dan_to_sphere_outer(point: Vec3D, sphere_center: Vec3D, sphere_radius: Float):
#     return {
#         distance: length(point - sphere_center) - sphere_radius
#         normal: normalize(point - sphere_center)
#     }
#
# def dan_to_arena_quarter(point: Vec3D):
# // Ground
# let dan = dan_to_plane(point, (0, 0, 0), (0, 1, 0))
# // Ceiling
# dan = min(dan, dan_to_plane(point, (0, arena.height, 0), (0, -1, 0)))
# // Side x
# dan = min(dan, dan_to_plane(point, (arena.width / 2, 0, 0), (-1, 0, 0)))
# 11
# // Side z (goal)
# dan = min(dan, dan_to_plane(
# point,
# (0, 0, (arena.depth / 2) + arena.goal_depth),
# (0, 0, -1)))
# // Side z
# let v = (point.x, point.y) - (
# (arena.goal_width / 2) - arena.goal_top_radius,
# arena.goal_height - arena.goal_top_radius)
# if point.x >= (arena.goal_width / 2) + arena.goal_side_radius
# or point.y >= arena.goal_height + arena.goal_side_radius
# or (
# v.x > 0
# and v.y > 0
# and length(v) >= arena.goal_top_radius + arena.goal_side_radius):
# dan = min(dan, dan_to_plane(point, (0, 0, arena.depth / 2), (0, 0, -1)))
# // Side x & ceiling (goal)
# if point.z >= (arena.depth / 2) + arena.goal_side_radius:
# // x
# dan = min(dan, dan_to_plane(
# point,
# (arena.goal_width / 2, 0, 0),
# (-1, 0, 0)))
# // y
# dan = min(dan, dan_to_plane(point, (0, arena.goal_height, 0), (0, -1, 0)))
# // Goal back corners
# assert arena.bottom_radius == arena.goal_top_radius
# if point.z > (arena.depth / 2) + arena.goal_depth - arena.bottom_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# clamp(
# point.x,
# arena.bottom_radius - (arena.goal_width / 2),
# (arena.goal_width / 2) - arena.bottom_radius,
# ),
# clamp(
# point.y,
# arena.bottom_radius,
# arena.goal_height - arena.goal_top_radius,
# ),
# (arena.depth / 2) + arena.goal_depth - arena.bottom_radius),
# arena.bottom_radius))
# // Corner
# if point.x > (arena.width / 2) - arena.corner_radius
# and point.z > (arena.depth / 2) - arena.corner_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# (arena.width / 2) - arena.corner_radius,
# point.y,
# (arena.depth / 2) - arena.corner_radius
# 12
# ),
# arena.corner_radius))
# // Goal outer corner
# if point.z < (arena.depth / 2) + arena.goal_side_radius:
# // Side x
# if point.x < (arena.goal_width / 2) + arena.goal_side_radius:
# dan = min(dan, dan_to_sphere_outer(
# point,
# (
# (arena.goal_width / 2) + arena.goal_side_radius,
# point.y,
# (arena.depth / 2) + arena.goal_side_radius
# ),
# arena.goal_side_radius))
# // Ceiling
# if point.y < arena.goal_height + arena.goal_side_radius:
# dan = min(dan, dan_to_sphere_outer(
# point,
# (
# point.x,
# arena.goal_height + arena.goal_side_radius,
# (arena.depth / 2) + arena.goal_side_radius
# ),
# arena.goal_side_radius))
# // Top corner
# let o = (
# (arena.goal_width / 2) - arena.goal_top_radius,
# arena.goal_height - arena.goal_top_radius
# )
# let v = (point.x, point.y) - o
# if v.x > 0 and v.y > 0:
# let o = o + normalize(v) * (arena.goal_top_radius + arena.goal_side_radius)
# dan = min(dan, dan_to_sphere_outer(
# point,
# (o.x, o.y, (arena.depth / 2) + arena.goal_side_radius),
# arena.goal_side_radius))
# // Goal inside top corners
# if point.z > (arena.depth / 2) + arena.goal_side_radius
# and point.y > arena.goal_height - arena.goal_top_radius:
# // Side x
# if point.x > (arena.goal_width / 2) - arena.goal_top_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# (arena.goal_width / 2) - arena.goal_top_radius,
# arena.goal_height - arena.goal_top_radius,
# point.z
# ),
# arena.goal_top_radius))
# // Side z
# if point.z > (arena.depth / 2) + arena.goal_depth - arena.goal_top_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# 13
# point.x,
# arena.goal_height - arena.goal_top_radius,
# (arena.depth / 2) + arena.goal_depth - arena.goal_top_radius
# ),
# arena.goal_top_radius))
# // Bottom corners
# if point.y < arena.bottom_radius:
# // Side x
# if point.x > (arena.width / 2) - arena.bottom_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# (arena.width / 2) - arena.bottom_radius,
# arena.bottom_radius,
# point.z
# ),
# arena.bottom_radius))
# // Side z
# if point.z > (arena.depth / 2) - arena.bottom_radius
# and point.x >= (arena.goal_width / 2) + arena.goal_side_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# point.x,
# arena.bottom_radius,
# (arena.depth / 2) - arena.bottom_radius
# ),
# arena.bottom_radius))
# // Side z (goal)
# if point.z > (arena.depth / 2) + arena.goal_depth - arena.bottom_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# point.x,
# arena.bottom_radius,
# (arena.depth / 2) + arena.goal_depth - arena.bottom_radius
# ),
# arena.bottom_radius))
# // Goal outer corner
# let o = (
# (arena.goal_width / 2) + arena.goal_side_radius,
# (arena.depth / 2) + arena.goal_side_radius
# )
# let v = (point.x, point.z) - o
# if v.x < 0 and v.y < 0
# and length(v) < arena.goal_side_radius + arena.bottom_radius:
# let o = o + normalize(v) * (arena.goal_side_radius + arena.bottom_radius)
# dan = min(dan, dan_to_sphere_inner(
# point,
# (o.x, arena.bottom_radius, o.y),
# arena.bottom_radius))
# // Side x (goal)
# if point.z >= (arena.depth / 2) + arena.goal_side_radius
# and point.x > (arena.goal_width / 2) - arena.bottom_radius:
# dan = min(dan, dan_to_sphere_inner(
# 14
# point,
# (
# (arena.goal_width / 2) - arena.bottom_radius,
# arena.bottom_radius,
# point.z
# ),
# arena.bottom_radius))
# // Corner
# if point.x > (arena.width / 2) - arena.corner_radius
# and point.z > (arena.depth / 2) - arena.corner_radius:
# let corner_o = (
# (arena.width / 2) - arena.corner_radius,
# (arena.depth / 2) - arena.corner_radius
# )
# let n = (point.x, point.z) - corner_o
# let dist = n.len()
# if dist > arena.corner_radius - arena.bottom_radius:
# let n = n / dist
# let o2 = corner_o + n * (arena.corner_radius - arena.bottom_radius)
# dan = min(dan, dan_to_sphere_inner(
# point,
# (o2.x, arena.bottom_radius, o2.y),
# arena.bottom_radius))
# // Ceiling corners
# if point.y > arena.height - arena.top_radius:
# // Side x
# if point.x > (arena.width / 2) - arena.top_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# (arena.width / 2) - arena.top_radius,
# arena.height - arena.top_radius,
# point.z,
# ),
# arena.top_radius))
# // Side z
# if point.z > (arena.depth / 2) - arena.top_radius:
# dan = min(dan, dan_to_sphere_inner(
# point,
# (
# point.x,
# arena.height - arena.top_radius,
# (arena.depth / 2) - arena.top_radius,
# )
# arena.top_radius))
# // Corner
# if point.x > (arena.width / 2) - arena.corner_radius
# and point.z > (arena.depth / 2) - arena.corner_radius:
# let corner_o = (
# (arena.width / 2) - arena.corner_radius,
# (arena.depth / 2) - arena.corner_radius
# )
# let dv = (point.x, point.z) - corner_o
# if length(dv) > arena.corner_radius - arena.top_radius:
# 15
# let n = normalize(dv)
# let o2 = corner_o + n * (arena.corner_radius - arena.top_radius)
# dan = min(dan, dan_to_sphere_inner(
# point,
# (o2.x, arena.height - arena.top_radius, o2.y),
# arena.top_radius))
# return dan
# }
# def dan_to_arena(point: Vec3D):
# let negate_x = point.x < 0
# let negate_z = point.z < 0
# if negate_x:
# point.x = -point.x
# if negate_z:
# point.z = -point.z
# let result = dan_to_arena_quarter(point)
# if negate_x:
# result.normal.x = -result.normal.x
# if negate_z:
# result.normal.z = -result.normal.z
# return result