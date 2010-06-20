
import os.path
import random

from pyGBot.Plugins.games.mafiafiles import load, dump
from pyGBot.Plugins.games.mafiafiles.players import PlayerData

roleset = load(open(os.path.join(os.path.dirname(__file__), "roles.yaml"), "r"))
setups = load(open(os.path.join(os.path.dirname(__file__), "setups.yaml"), "r"))

def generate_setup(game):
    def rolesort(role):
        return roles[role].get('importance', 1)

    setup = dict(setups.get('AllSetups', {}))
    setup.update(setups[game.setup])
    game.setup = setup

    roles = dict((k, v) for k, v in roleset.iteritems() if k in setup.get('roles', roleset.keys()))
    axes  = {}

    for name, data in setup.get('override', {}):
        roles[name].update(data)

    rolebase = roles.get('AllRoles', {})
    defaults = setup.get('defaults', {})
    override = setup.get('override', {}).get('AllRoles', {})
    for name, roledata in roles.iteritems():
        role = dict(rolebase)
        role.update(defaults)
        role.update(roledata)
        role.update(override)
        axes.setdefault(role['axis'], {'roles': []})['roles'].append(name)

    maxratio = float(sum(data['ratio'] for data in setup['axes'].itervalues()))
    playercount = len(game.queue)

    for axis, data in setup['axes'].iteritems():
        D = axes[axis]
        D.update(data)
        D['roles'].sort(key=rolesort)
        D['workroles'] = D['roles'][:]
        D['ratio'] = int(round(data['ratio'] / maxratio * playercount))

    weightaxes = [axis for axis, data in axes.iteritems() for _ in xrange(data['ratio'])]
    random.shuffle(weightaxes)

    weightroles = []
    for axis in weightaxes:
        if not axes[axis]['workroles']:
            axes[axis]['workroles'] = [R for R in axes[axis]['roles'][:] if roles[R].get('max', True)]
        role = axes[axis]['workroles'].pop()
        if 'max' in roles[role]:
            roles[role]['max'] -= 1
        weightroles.append(role)

    game.players = {}
    for nick, axis, role in zip(game.queue, weightaxes, weightroles):
        player = PlayerData(game, nick, axis, role)
        game.players.append(player)

