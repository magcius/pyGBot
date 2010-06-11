import string

def testsetup(game):
    game.playerlist = []
    game.setups = {'default':{'maxnum':0, 'minimum':4, 'starttime':'night', 'anon':False, 'daytimer':None, 'defaultmafioso':33, 'setup':{4:{'Doctor':1},5:{'Doctor':1,'Sheriff':1}}}}
    for i in range(int(param[0])):
        game.playerlist.append(string.ascii_lowercase[i])
        
def forcecommands(game,channel, user, param):
    game.runNightCommands()
    
def forceplayerdata(game, channel, user, param):
    if not param: param = [5]
    testsetup(game)
    game.createPlayerData(channel, user)

def forcestart(game, channel, user, param):
    game.setups = {'default':{'maxnum':0, 'minimum':4, 'starttime':'night', 'anon':False, 'daytimer':None, 'defaultmafioso':33, 'setup':{4:{'Doctor':1},5:{'Doctor':1,'Sheriff':1}}}}
    #testsetup(game)
    game.startSetup(channel, user, param)
