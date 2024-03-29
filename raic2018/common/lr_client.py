import os
import time
import subprocess
import socket
import random
from typing import List, Optional, Dict

from model import Game, Action
from RemoteProcessClient import RemoteProcessClient
from enum import Enum
import copy
import atexit


ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
HIGH_PRIORITY_CLASS         = 0x00000080
IDLE_PRIORITY_CLASS         = 0x00000040
NORMAL_PRIORITY_CLASS       = 0x00000020
REALTIME_PRIORITY_CLASS     = 0x00000100


class Winner(Enum):
    First = 0
    Second = 1


class LocalRunnerClient:
    def __init__(self, two_player=True):
        self.two_player = two_player
        ports = [random.randrange(10000, 65535) for _ in range(2 if two_player else 1)]
        cur_path = os.path.dirname(os.path.realpath(__file__))
        lr_path = f'{cur_path}/../../localrunner/codeball2018.exe'
        args = [lr_path, '--noshow', '--no-countdown', '--duration', str(2_000_000_000), '--team-size', '1',
                '--p1', f'tcp-{ports[0]}',
                '--p2', f'tcp-{ports[1]}' if two_player else 'helper']
        self._proc = subprocess.Popen(args, creationflags=BELOW_NORMAL_PRIORITY_CLASS, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        atexit.register(lambda p: p.kill(), self._proc)
        self._proc.stdout.readline()
        self._proc.stdout.readline()
        time.sleep(2)
        self._clients = [RemoteProcessClient('127.0.0.1', p) for p in ports]

        for client in self._clients:
            client.write_token("0000000000000000")
        self._first_step = True
        self._waiting_for_actions = False
        self.rules = self._clients[0].read_rules()
        self._p1_game = self._clients[0].read_game()

    def get_states(self):
        assert not self._waiting_for_actions
        self._waiting_for_actions = True

        if self.two_player:
            return [self._p1_game, self._reverse_side(self._p1_game)]
        else:
            return [self._p1_game]

    def act(self, actions: Dict[int, Action]) -> Optional[Winner]:
        assert self._waiting_for_actions
        self._waiting_for_actions = False

        # p1 actions
        p1_robot_ids = [r.id for r in self._p1_game.robots if r.is_teammate]
        p1_actions = {id: ac for id, ac in actions.items() if id in p1_robot_ids}
        assert len(p1_robot_ids) == len(p1_actions)
        self._clients[0].write(p1_actions)

        # p2 actions
        if self.two_player:
            if self._first_step:
                self._clients[1].read_rules()
                self._first_step = False
            self._clients[1].read_game()
            p2_actions = {id: ac for id, ac in actions.items() if id not in p1_robot_ids}
            assert len(p1_actions) == len(p2_actions)
            self._clients[1].write(p2_actions)
        else:
            assert len(p1_actions) == len(actions)

        # get new game state
        prev_scores = [p.score for p in self._p1_game.players]
        self._p1_game = self._clients[0].read_game()
        assert self._p1_game.players[0].me
        assert not any(p.strategy_crashed for p in self._p1_game.players)
        cur_scores = [p.score for p in self._p1_game.players]

        # return winner
        if cur_scores[0] > prev_scores[0]:
            return Winner.First
        elif cur_scores[1] > prev_scores[1]:
            return Winner.Second
        return None

    def _reverse_side(self, game: Game) -> Game:
        game = copy.deepcopy(game)
        for p in game.players:
            p.me = not p.me
        for r in game.robots:
            r.is_teammate = not r.is_teammate
            r.z *= -1
            r.velocity_z *= -1
            r.touch_normal_z *= -1
        for n in game.nitro_packs:
            n.z *= -1
        game.ball.z *= -1
        game.ball.velocity_z *= -1
        return game

    def __del__(self):
        self._proc.kill()
