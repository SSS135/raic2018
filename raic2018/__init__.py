import sys
import os

curdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, curdir)
sys.path.insert(1, os.path.join(curdir, os.pardir))


try:
    from gym.envs.registration import register
    register(
        id='CodeBallHelper-v0',
        entry_point='raic2018.common.single_player_env:HelperEnv',
    )
    register(
        id='CodeBallHelperFrameSkip-v0',
        entry_point='raic2018.common.single_player_env:HelperFrameSkipEnv',
    )
except:
    pass