import pickle
from collections import OrderedDict

import torch
import sys
from ppo_pytorch.models import FCActor, Actor
from torch import nn


def pytorch_to_numpy(pt_path, np_path):
    model: Actor = torch.load(pt_path)
    if isinstance(model, FCActor):
        activation = model.activation.__name__
        model: OrderedDict = model.state_dict()
        model['activation'] = activation
    else:
        raise NotImplementedError
    model = {k: v.cpu().numpy() if torch.is_tensor(v) else v for (k, v) in model.items()}
    with open(np_path, 'w+b') as file:
        pickle.dump(model, file)


if __name__ == '__main__':
    inp = sys.argv[1]
    outp = sys.argv[2]
    print(f'converting "{inp}" -> "{outp}"')
    pytorch_to_numpy(inp, outp)