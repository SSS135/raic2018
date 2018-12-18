import os
import random
import time
from collections import OrderedDict

from .bot_env import MadCarsAIEnv
from ..bots.torch_nn_bot import TorchBotStrategy


class MadCarsNNEnv(MadCarsAIEnv):
    root_folder = './pop_models'
    new_model_check_interval = 60
    num_last_models_used = 20

    def __init__(self):
        super().__init__()
        self.models: OrderedDict[str, TorchBotStrategy] = OrderedDict()
        self.all_used_models = set()
        self.models_refresh_time = 0

    def _get_bot(self):
        self._check_refresh_models()
        if len(self.models) > 0:
            return random.choice(list(self.models.values()))
        else:
            return super()._get_bot()

    def _check_refresh_models(self):
        if self.models_refresh_time + self.new_model_check_interval > time.time():
            return
        self.models_refresh_time = time.time()

        model_files = [os.path.join(self.root_folder, f) for f in os.listdir(self.root_folder)]
        model_files = [f for f in model_files if os.path.splitext(f)[1] == '.pth' and f not in self.all_used_models]
        model_files.sort(key=os.path.getctime)
        self.all_used_models.update(model_files)
        for file in model_files:
            self.models[file] = TorchBotStrategy(file)
            print(f'MadCarsNNEnv: added model {file}')
        while len(self.models) > self.num_last_models_used:
            file, model = self.models.popitem(False)
            print(f'MadCarsNNEnv: removed model {file}')
