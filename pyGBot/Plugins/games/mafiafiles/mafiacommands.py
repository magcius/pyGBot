import string
def check(game, channel, user, param, priority=2):
    target = param[0]
    game.queue(priority, user, "checkDO(self, '%s', '%s')"%(target,user))
    #game.speak(user, "You will find out the results in the morning")

def kill(game, channel, user, param, priority=3):
    target = param[0]
    game.queue(priority, user, "killDO(self, '%s', '%s')"%(target,user))
#    mafiatargetlist = []
#    mafiosolist = []
#    for member in game.mafialist:
#        if game.playerdata[member]['role'].returnName() == "Mafioso":
#            mafiosolist.append(member)
#            if game.playerdata[member]['role'].returnTarget() != None:
#                mafiatargetlist.append(game.playerdata[member]['role'].returnTarget())
#    game.speak(mafiosolist, "%s has voted to kill %s!"%(user,target))
#    mafiatargetlist.append(target)
#    if mafiatargetlist == [mafiatargetlist[0]]*len(mafiosolist):
#        killer = random.choice(game.mafialist)
#        game.speak(game.mafialist, "The council has decided that %s must die. They have also determined that %s is the man for the job. Do not fail.",private=True)
#        game.queue(priority, killer, "killDO(self, %s, %s)"%(target,user))

     
            
def checkDO(game, target, user):
    game.speak(user, '')
#    game.send(user, game.playerdata[target.lower()]['role'].returnFileSays())
#    return True

def killDO(game, target, user):
    game.speak(user, 'going to kill target')
    #if target == 'none'
    #if game.playerdata[target.lower()]['saved'] = False:
    #    game.playerDie(game, target)
        
