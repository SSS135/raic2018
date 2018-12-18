
class MyStrategy:
    def act(self, me, rules, game, action):
        action.target_velocity_z = 1
        action.target_velocity_x = -1