
import sys, string, random, time, re, itertools

from twisted.python import log
from pygbot.baseplugiev import BasePlugin, autoConnect

class plugin(BasePlugin):
    def __init__(self, bot, channel, config):
        self.bot = bot
        self.gamestatus = None
        self.gamestarter = None
        self.setup = None
        self.players = []
        self.settings = {}
        self.queue = None

        self.test = False              # Hopefully for creating tests of setups, with arbitrary players

    def start_game(self, channel, user, params):
        if channel != self.channel:
            return

        if self.queue is None:
            self.queue = []

command_handlers = {
    "start": Mafia2.start_game,
    "end": Mafia2.end_game,
    "status": Mafia2.status,
    "set": Mafia2.set_settings,
    "join": Mafia2.join,
    "quit": Mafia2.quit,
}
