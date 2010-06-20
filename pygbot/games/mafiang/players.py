
from random import choice

class PlayerData(object):
    def __init__(self, game, nick, axis, role):
        self.game, self.nick, self.axis = game, nick, axis
        self.initialize_role(role)

    def privout(self, message):
        self.game.privout(self.nick, message)

    pubout = privout

    def noteout(self, message):
        self.game.noteout(self.nick, message)

    def initialize_role(self, role):
        self._role = role
        self.nightactions = []
        self.dayactions = []
        for key, value in role.iteritems():
            setattr(self, key, value)
        random = role.get('random', {})

        if 'nightactions' in random:
            self.nightactions.append(choice(random.get('nightactions', [])))

        if 'dayactions' in random:
            self.dayactions.append(choice(random.get('dayactions', [])))
