import asyncio
from asyncio import events
from queue import Queue
from threading import Thread

from ..mechanic.game import Game
from ..mechanic.strategy import Client


class DetachedClient(Client):
    def __init__(self):
        self.message_queue = Queue()
        self.command_queue = Queue()

    @asyncio.coroutine
    def get_command(self):
        cmd = self.command_queue.get(timeout=60)
        return cmd

    def send_message(self, t, d):
        self.message_queue.put((t, d))


class BotClient(Client):
    def __init__(self, strategy):
        self.strategy = strategy
        self.command = None

    @asyncio.coroutine
    def get_command(self):
        return self.command

    def send_message(self, t, d):
        self.command = self.strategy.receive_message(t, d)


class NoGraphicsGame(Game):
    def draw(self, draw_options):
        pass

    def game_save(self):
        pass


class DetachedGame:
    def __init__(self, game: Game):
        self.game = game
        self.thread = Thread(target=self._run_thread)
        self.thread.start()

    @property
    def done(self):
        return self.game.game_complete

    @property
    def winner(self) -> Client:
        assert self.done
        winner = self.game.get_winner()
        return self.game.get_winner().client if winner else None

    def _run_thread(self):
        loop = events.new_event_loop()
        events.set_event_loop(loop)

        while not self.done:
            loop.run_until_complete(self.game.tick())