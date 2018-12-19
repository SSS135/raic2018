# def collide_entities(a: Entity, b: Entity):
#     delta_position = b.position - a.position
#     distance = length(delta_position)
#     penetration = a.radius + b.radius - distance
#     if penetration > 0:
#         k_a = (1 / a.mass) / ((1 / a.mass) + (1 / b.mass))
#         k_b = (1 / b.mass) / ((1 / a.mass) + (1 / b.mass))
#         normal = normalize(delta_position)
#         a.position -= normal * penetration * k_a
#         b.position += normal * penetration * k_b
#         delta_velocity = dot(b.velocity - a.velocity, normal) + b.radius_change_speed - a.radius_change_speed
#         if delta_velocity < 0:
#             impulse = (1 + random(MIN_HIT_E, MAX_HIT_E)) * delta_velocity * normal
#             a.velocity += impulse * k_a
#             b.velocity -= impulse * k_b
#
#
# def collide_with_arena(e: Entity):
#     distance, normal = dan_to_arena(e.position)
#     penetration = e.radius - distance
#     if penetration > 0:
#         e.position += penetration * normal
#         velocity = dot(e.velocity, normal) - e.radius_change_speed
#         if velocity < 0:
#             e.velocity -= (1 + e.arena_e) * velocity * normal
#             return normal
#     return None
#
#
# def move(e: Entity):
#     e.velocity = clamp(e.velocity, MAX_ENTITY_SPEED)
#     e.position += e.velocity * delta_time
#     e.position.y -= GRAVITY * delta_time * delta_time / 2
#     e.velocity.y -= GRAVITY * delta_time
#
#
# def update(delta_time: float):
#     shuffle(robots)
#
#     for robot in robots:
#         if robot.touch:
#             target_velocity = clamp(
#                 robot.action.target_velocity,
#                 ROBOT_MAX_GROUND_SPEED)
#             target_velocity -= robot.touch_normal * dot(robot.touch_normal, target_velocity)
#             target_velocity_change = target_velocity - robot.velocity
#             if length(target_velocity_change) > 0:
#                 acceleration = ROBOT_ACCELERATION * max(0, robot.touch_normal.y)
#                 robot.velocity += clamp(
#                     normalize(target_velocity_change) * acceleration * delta_time,
#                     length(target_velocity_change))
#
#         if robot.action.use_nitro:
#             target_velocity_change = clamp(
#                 robot.action.target_velocity - robot.velocity,
#                 robot.nitro * NITRO_POINT_VELOCITY_CHANGE)
#             if length(target_velocity_change) > 0:
#                 acceleration = normalize(target_velocity_change) * ROBOT_NITRO_ACCELERATION
#                 velocity_change = clamp(
#                     acceleration * delta_time,
#                     length(target_velocity_change))
#                 robot.velocity += velocity_change
#                 robot.nitro -= length(velocity_change) / NITRO_POINT_VELOCITY_CHANGE
#         move(robot)
#         robot.radius = ROBOT_MIN_RADIUS + (ROBOT_MAX_RADIUS - ROBOT_MIN_RADIUS) * robot.action.jump_speed / ROBOT_MAX_JUMP_SPEED
#         robot.radius_change_speed = robot.action.jump_speed
#
#     move(ball)
#
#     for i in range(len(robots)):
#         for j in range(i):
#             collide_entities(robots[i], robots[j])
#
#     for robot in robots:
#         collide_entities(robot, ball)
#         collision_normal = collide_with_arena(robot)
#         if collision_normal is None:
#             robot.touch = false
#         else:
#             robot.touch = true
#             robot.touch_normal = collision_normal
#
#     collide_with_arena(ball)
#
#     if abs(ball.position.z) > arena.depth / 2 + ball.radius:
#         goal_scored()
#
#     for robot in robots:
#         if robot.nitro == MAX_NITRO_AMOUNT:
#             continue
#         for pack in nitro_packs:
#             if not pack.alive:
#                 continue
#             if length(robot.position - pack.position) <= robot.radius + pack.radius:
#                 robot.nitro = MAX_NITRO_AMOUNT
#                 pack.alive = false
#                 pack.respawn_ticks = NITRO_PACK_RESPAWN_TICKS
#
#
# def tick():
#     delta_time = 1 / TICKS_PER_SECOND
#     for _ in range(MICROTICKS_PER_TICK):
#         update(delta_time / MICROTICKS_PER_TICK)
#
#     for pack in nitro_packs:
#         if pack.alive:
#             continue
#         pack.respawn_ticks -= 1
#         if pack.respawn_ticks == 0:
#             pack.alive = true