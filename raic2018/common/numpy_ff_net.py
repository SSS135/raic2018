import pickle
from itertools import count

import numpy as np
import numpy.random as rng


SOFTMAX_MULT = 1


def softmax(x: np.ndarray) -> np.ndarray:
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=-1)


def relu(x: np.ndarray) -> np.ndarray:
    x = x.copy()
    x[x < 0] = 0
    return x


def elu(x: np.ndarray, alpha=1) -> np.ndarray:
    x = x.copy()
    neg_indices = x[0] < 0
    x[neg_indices] = alpha * (np.exp(x[neg_indices]) - 1)
    return x


ACTIVATIONS = {
    'Tanh': np.tanh,
    'ELU': elu,
    'ReLU': relu,
}


class FFNet:
    def __init__(self, model_path):
        with open(model_path, 'rb') as file:
            self.data = pickle.load(file)
        self.activation = ACTIVATIONS[self.data.get('activation', 'Tanh')]

    @property
    def input_size(self):
        return self.data['linear.0.0.weight'].shape[1]

    def __call__(self, x):
        for i in count():
            weight_name = str.format('linear.{}.0.weight', i)
            bias_name = str.format('linear.{}.0.bias', i)
            if weight_name not in self.data:
                break
            x = self.data[weight_name] @ x + self.data[bias_name]
            x = self.activation(x)

        probs_weight = self.data['head_probs.linear.weight']
        probs_bias = self.data['head_probs.linear.bias']

        probs = probs_weight @ x + probs_bias
        probs = softmax(probs * SOFTMAX_MULT)
        action = rng.choice(len(probs), p=probs)

        return action