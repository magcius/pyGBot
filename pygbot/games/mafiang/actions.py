
class Action(object):
    def __init__(self, game, player):
        self.game, self.player = game, players

class Kill(Action):
    def do(self):
        self.game.players
