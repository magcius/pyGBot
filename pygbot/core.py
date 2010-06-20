##
##    pyGBot - Versatile IRC Bot
##    Copyright (C) 2008-2010 Morgan Lokhorst-Blight, Alex Soborov, Paul Rotering, Jasper St. Pierre
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

import hashlib
import inspect

import pygbot

from pygbot import irc3
from pygbot.baseplugin import event, EventListener, IGBotPlugin

from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.plugin import getPlugins

# IRC formatting
BOLD      = '\x02' # Bold
UNDERLINE = '\x1F' # Underline
REV_VIDEO = '\x16' # Reverse Video
mIRC_COL  = '\x03' # mIRC coloring

def format_message(message):
    for msg in message.strip().splitlines():
        if "%S" in msg:
            msg = msg.replace("%S", "")
        if msg == '': msg = '   '
        else:
            msg = msg.strip()
        yield (msg
               .replace('%C', mIRC_COL)
               .replace('%B', BOLD)
               .replace('%U', UNDERLINE)
               .replace('%V', REV_VIDEO))


class Channel(irc3.Channel, EventListener):
    def __init__(self, bot, target):
        irc3.Channel.__init__(self, bot, target)
        EventListener.__init__(self, bot)
        self.plugins = []

    def loadConfiguration(self, config):
        if 'Autojoin' in config:
            self.connectionMade = self.autojoin

        factories = self.bot.pluginClasses
        for name, conf in config['Plugins'].iteritems():
            if name in factories:
                self.plugins.append(factories[name](self.bot, self, conf))

    def autojoin(self):
        self.bot.join(self)

    def activate(self):
        EventListener.activate(self)
        for plugin in self.plugins:
            plugin.activate()

    def deactivate(self):
        EventListener.deactivate(self)
        for plugin in self.plugins:
            plugin.deactivate()

class User(irc3.User, EventListener):
    def __init__(self, bot, target):
        irc3.Channel.__init__(self, bot, target)
        EventListener.__init__(self, bot)

    @property
    def channels(self):
        return [ch for ch in self.bot.channels if self in ch.user]

    def test_auth(self, guess):
        answer, salt = self.auth
        digest = hashlib.sha1(guess).hexdigest()
        if salt:
            digest = hashlib.sha1(digest + salt).hexdigest()
            return answer == digest

class GBot(irc3.IRCClient, object):
    sourceURL   = "http://github.com/magcius/pyGBot/tree/ng"
    versionName = "pygbot-ng"
    versionNum  = "latest"
    versionEnv  = "twisted"

    __events__ = ['connectionMade', 'connectionLost', 'joined', 'left', 'kickedFrom',
                  'noticed', 'action', 'topicUpdated', 'userJoined', 'userLeft',
                  'userKicked', 'userQuit', 'userRenamed', 'privateMessage', 'publicMessage',
                  'message']

    channelFactory = Channel
    userFactory = User

    def __init__(self):
        irc3.IRCClient.__init__(self)
        self.listeners = set()
        self.loadPlugins()
        self.createEvents()

    def createEvents(self):
        for name in self.__events__:
            originalFunc = getattr(self, name, None)
            newevent = event(name)
            if originalFunc:
                args = inspect.getargspec(originalFunc)
                if "user" in args:
                    userindex = args.index('user')
                    def wrap(func):
                        def inner(*a, **kw):
                            user = self.user(kw.pop('user', None) or a[userindex])
                            func(user=user, *a, **kw)
                        return inner
                    newevent = wrap(newevent)
                if "channel" in args:
                    chanindex = args.index('channel')
                    def wrap(func):
                        def inner(*a, **kw):
                            channel = self.channel(kw.pop('channel', None) or a[chanindex])
                            func(channel=channel, *a, **kw)
                        return inner
                    newevent = wrap(newevent)
            setattr(self, name, newevent)

    # Yes, dispatchEvent is an event.
    @event
    def dispatchEvent(self, name, *a, **kw):
        for registry in self.listeners:
            for func in dict(registry).get(name, []):
                func(*a, **kw)

    def pubout(self, channel, message):
        for line in format_message(message):
            self.say(channel, line)

    def privout(self, user, message):
        for line in format_message(message):
            self.msg(user, line)

    def noteout(self, target, message):
        for line in format_message(message):
            self.notice(target, line)

    def invite(self, user, channel):
        self.sendLine("INVITE %s %s" % (user, channel))

    def modestring(self, target, modestring):
        self.sendLine("MODE %s %s" % (target, modestring))

    def cprivmsg(self, chan, user, message):
        self.sendLine("CPRIVMSG %s %s :%s" % (user, chan, message))

    def cnotice(self, chan, user, message):
        self.sendLine("CNOTICE %s %s :%s" % (user, chan, message))

    def loadConfiguration(self, config):
        self.nickname = config.get("Nickname", self.nickname)
        self.realname = config.get("Realname", self.realname)
        self.username = config.get("Username", self.username)
        self.password = config.get("Password", self.password)

        self.sourceURL = config.get("SourceURL", self.sourceURL)

        self.versionName = config.get("VersionName", self.versionName)
        self.versionNum = config.get("VersionNum", self.versionNum)
        self.versionEnv = config.get("VersionEnv", self.versionEnv)

        self.loadChannels(config.get('Channels', []))
        self.loadUsers(config.get('Users', []))

    def loadChannels(self, config):
        for name, data in config.iteritems():
            self.channels[name] = channel = self.channel(name)
            channel.loadConfiguration(data)

    def loadUsers(self, config):
        for nick, data in config.iteritems():
            if 'Hash' not in data: continue
            user = self.user(name)
            user.auth = data['Hash'], data.get('Salt', None)
            user.role = data.get('Role', 30)

    def loadPlugins(self):
        self.pluginclasses = {}
        for plugin in getPlugins(IGBotPlugin, pygbot):
            self.pluginclasses[plugin.__name__] = plugin
            plugin_name = "%s.%s" % (plugin.__module__, plugin.__name__)

class GBotIrcFactory(protocol.ReconnectingClientFactory):
    protocol = GBot

    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        p.loadConfiguration(self.config)
        return p
