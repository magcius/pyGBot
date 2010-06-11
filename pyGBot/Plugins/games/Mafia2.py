import sys, string, random, time, re, itertools
import pyGBot.Plugins.games.mafiafiles.mafiacommands as mafcmds
import pyGBot.Plugins.games.mafiafiles.testing as test
import pyGBot.Plugins.games.mafiafiles.roles as roles

from pyGBot import log
from pyGBot.BasePlugin import BasePlugin


class Mafia2(BasePlugin):
    def __init__(self, bot, options):
        self.gamestatus = "None"
        self.gamestarter = ''
        self.bot = bot
        self.nightcommands = []        # Queue of all commands to be performed at the end of night
        self.playerlist = []           # Contains list of all players in game during setup
        self.setups = {}               # Holds all data for setups, as parsed from file in later function
        self.playerdata = {}           # Holds all ingame data, including player role, if they're saved, if they're roleblocked, alive, possible nightactions, day actions
        self.playstyle = 'default'     # Setup
        self.starttime = None          # Start game day or night. Default in game setup
        self.anon = False              # Anon voting? Default in game setup
        self.daytimer = 0              # Day timer. Default in game setup.
        
        self.test = False              # Hopefully for creating tests of setups, with arbitrary players
    
    def activate(self, channel=None):          # Activated by pyGBot core when using command ^start Mafia2
        self.channel = channel
        #self.__init__(bot)
    
    def createPlayerData(self, channel, user):
        """
        Assigns roles and creates self.playerdata.
        """
        rolelist = []
        numplayers = len(self.playerlist)
        if self.playstyle in self.setups.keys():
            if self.setups[self.playstyle]['maxnum'] != 0 and numplayers > self.setups[self.playstyle]['maxnum']:
                self.speak(channel, "%s: \x02-Setup Error-\x02 Too many players for this setup. Maximum number of players for \x02%s\x02: %d"%(user, self.playstyle, self.setups[self.playstyle]['maxnum']))
                return 0
            elif numplayers < self.setups[self.playstyle]['minimum']:
                self.speak(channel, "%s: \x02-Setup Error-\x02 Too few players for this setup. Minimum number of players for \x02%s\x02: %d"%(user, self.playstyle, self.setups[self.playstyle]['minimum']))
                return 0
            else:
                mafiosopercent = float(self.setups[self.playstyle]['defaultmafioso'])/float(100)
                if self.starttime != None:
                    self.starttime = self.setups[self.playstyle]['starttime']
                if numplayers > max(self.setups[self.playstyle]['setup'].keys()):
                    numplayers = max(self.setups[self.playstyle]['setup'].keys())
                for role in self.setups[self.playstyle]['setup'][numplayers]:
                    for i in range(self.setups[self.playstyle]['setup'][numplayers][role]):
                        rolelist.append(role)
                numplayers =len(self.playerlist)
                nummafioso = int(mafiosopercent*numplayers)
                for i in range(nummafioso):
                    rolelist.append('Mafioso')
                leftover = numplayers-len(rolelist)
                for i in range(leftover):
                    rolelist.append('OrdinaryCitizen')
        random.shuffle(self.playerlist)
        random.shuffle(rolelist)
        for player in self.playerlist:
            role = rolelist.pop(0)
            exec("rolepath = roles."+role+"()")
            randomnightaction = rolepath.returnRandomNightActions()
            if len(randomnightaction) > 0:
                randomnightaction = list(random.choice(randomnightaction))
            else: randomnightaction = []
            randomdayaction = rolepath.returnRandomDayActions()
            if len(randomdayaction) > 0:
                randomdayaction = list(random.choice(randomdayaction))
            else: randomnightaction = []
            randomoneaction = rolepath.returnRandomOneActions()
            if len(randomoneaction) > 0:
                randomoneaction = list(random.choice(randomoneaction))
            else: randomnightaction = []
            nightactions = rolepath.returnNightActions()+randomnightaction
            dayactions = rolepath.returnDayActions()+randomdayaction
            onetimeaction = rolepath.returnOneActions()+randomoneaction
            self.playerdata[player]={'role':rolepath,'saved':False,'roleblocked':False,'alive':True,'nightactions':nightactions,'dayactions':dayactions,'onetimeaction':onetimeaction}
        print(self.playerdata)
    
    def speak(self, to, message):
        message = str(message)
        if type(to) == str:
            if to.startswith('#'): self.bot.pubout(to, message)
            else: self.bot.noteout(to, message)
        elif type(to) == list or type(to) == tuple: 
            for person in to: 
                self.speak(person, message)
    
    def msg_channel(self, channel, user, message):
        if message.startswith('!'): cmd = message[1:]
        elif message.lower().startswith(self.bot.nickname): cmd = message.split(' ',1)[1]
        else: cmd = ''
        self.do_command(channel, user, cmd)
        
    def startParser(self, channel, user, params):
        if self.gamestatus == "None":
            self.startSetup(channel, user, params)
            
        
    def startSetup(self, channel, user, params):
        self.playstyle = 'default'
        self.gamestarter = user
        self.starttime = self.setups[self.playstyle]['starttime']
        self.anon = self.setups[self.playstyle]['anon']
        self.daytimer = self.setups[self.playstyle]['daytimer']
        if params:
            for item in params:
                item = item.lower().split('=')
                if item[0] == "setup":
                    if item[1].lower() in self.setups:
                        self.playstyle = params[0]
                        self.starttime = self.setups[self.playstyle]['starttime']
                        self.anon = self.setups[self.playstyle]['anon']
                        self.daytimer = self.setups[self.playstyle]['daytimer']
                    else:
                        self.speak(channel, "%s: \x02-Setup Error-\x02 Invalid setup. %s is not a valid setup. Use the help.setup command to get a list of all setups."(user,item[1]))
                        return 0
            if self.changeSettings(channel, user, params) == 0:
                return 0
        self.gamestatus = "Setup"
        self.printGameInfo(channel, user)

    def printGameInfo(self, channel, user):
        if self.setups[self.playstyle]['maxnum'] == 0: maxtext = "UNLIMITED"
        else: maxtext = str(self.setups[self.playstyle]['maxnum'])
        mintext = str(self.setups[self.playstyle]['minimum'])
        self.speak(channel, "%s: \x02Game Status: %s.\x02 \x02Round information\x02 -- \x02Setup:\x02 %s | \x02Starting State:\x02 %s | \x02Day Timer:\x02 %s | \x02 Anonymous Voting:\x02 %s | \x02Max player count:\x02  %s | \x02Minimum player count:\x02 %s"%(user, self.gamestatus, self.playstyle, self.starttime, self.daytimer, self.anon, maxtext, mintext))
        
    def changeSettings(self, channel, user, params):
        for item in params:
            item=item.lower().split('=')
            if item[0] == 'state':
                print item[1]
                if item[1] in ['day','night']:
                    self.starttime = item[1]
                else:
                    self.speak(channel, "%s: \x02-Setup Error-\x02 Invalid starting state. Use only 'day' or 'night'."%(user))
                    return 0
            if item[0] == 'anon':
                if item[1] in ['on','true']:
                    self.anon = True
                elif item[1] in ['off','false']:
                    self.anon = False
                else:
                    self.speak(channel, "%s: \x02-Setup Error-\x02 Invalid anonymous voting settings. Use only define it with 'on' or 'off'."%(user))
                    return 0
            if item[0] == 'timer':
                try:
                    if 0 <= int(item[1]) <= 120:
                        self.daytimer = int(item[1])
                    else:
                        self.speak(channel, "%s: \x02-Setup Error-\x02 Invalid day timer value. Use only an integer between 0 and 120."%(user))
                        return 0
                except ValueError:
                    self.speak(channel, "%s: \x02-Setup Error-\x02 Invalid day timer value. Use only an integer between 0 and 120."%(user))
                    return 0

        
    def joinGame(self, channel, user, params):
        if channel != self.channel:
            self.speak(channel, "%s: Please join the game in %s."%(user,self.channel))
            return 0
        
    def timer_tick(self):
        #called every second
        pass
        
        
#    def resetPlayerData(self):
#       for player in self.playerdata:
#           for aspect in player:
#               if player[aspect] == True and aspect != 'alive':
#                   player[aspect] = False
#           player['role'].changeHasActioned(False)

    def queue(self,priority, user, command):
        self.nightcommands.append((priority, user, command))
        
    def runNightCommands(self):
        self.nightcommands.sort()
        self.nightcommands.reverse()
        for command in self.nightcommands:
            if not self.playerdata[command[1].lower()]['roleblocked'] and self.playerdata[command[1].lower()]['alive']:
                exec("mafcmds."+command[2])
        self.nightcommands = []
        
    def do_command(self, channel, user, cmd):
        """This is the function called whenever someone sends a public or
        private message addressed to the bot. (e.g. "bot: blah").    Parse
        the CMD, execute it, then reply either to public channel or via
        /msg, based on how the command was received.    E is the original
        event, and FROM_PRIVATE is the nick that sent the message."""
        if cmd=='': return
        cmds = cmd.strip().split(" ")
        cmds[0]=cmds[0].lower()
        #if user in self.dead_players:
        #     if cmds[0] not in ("stats", "status", "help", "dchat", "end", "del"):
        #        self.speak(user, "Please -- dead players should keep quiet.")
        #        return 0
        if cmds[0].startswith('force'):
            cmdstring = "test."+ cmds[0]+"(self, '"+channel+"', '"+user+"',"+str(cmds[1:])+")"
            exec(cmdstring)
            return
        if not re.match("(start|status|stats|join|quit|end|settings) ",cmds[0]):
            cmdstring = "mafcmds." + cmds[0]+"(self, '"+channel+"', '"+user+"',"+str(cmds[1:])+")"
            exec(cmdstring)
        if cmds[0] == 'start':
            self.startParser(channel, user, cmd.split())
    
