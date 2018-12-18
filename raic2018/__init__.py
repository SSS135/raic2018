import sys
import os

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, curdir)
sys.path.insert(1, os.path.join(curdir, os.pardir))


try:
    from gym.envs.registration import register
    register(
        id='MadCarsAI-v0',
        entry_point='miniaicups_mad_cars.common.bot_env:MadCarsAIEnv',
        reward_threshold=0.9,
    )
    register(
        id='MadCarsNN-v0',
        entry_point='miniaicups_mad_cars.common.nn_env:MadCarsNNEnv',
        reward_threshold=0.9,
    )
    register(
        id='MadCarsMultiplayer-v0',
        entry_point='miniaicups_mad_cars.common.multiplayer_env:MadCarsMultiplayerEnv',
        reward_threshold=0.9,
    )
except:
    pass