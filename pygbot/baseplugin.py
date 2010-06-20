
import collections
import functools

from pygbot.commands import Command

from twisted.plugin import IPlugin
from twisted.python import log
from zope.interface import implements

def event(name_or_func):
    """
    Decorator that automatically dispatches the event when it is called.
    """
    if isinstance(name_or_func, collections.Callable):
        func, name = name_or_func, name_or_func.__name__
        @functools.wraps(func)
        def dispatcher(bot, *a, **kw):
            log.msg("Dispatching event %s(%s, %s)" % (name, a, kw))
            func(*a, **kw)
            bot.dispatchEvent(name, *a, **kw)
    else:
        def dispatcher(bot, *a, **kw):
            log.msg("Dispatching event %s(%s, %s)" % (name_or_func, a, kw))
            bot.dispatchEvent(name_or_func, *a, **kw)
    return dispatcher

def autoConnect(name_or_func):
    """
    Automatically connect this function to the
    appropriate event when the plugin's autoConnect
    function is called.

    Usage:

    >>> @autoConnect
    ... def publicMessage(self, user, channel, message):
    ...     pass

    >>> @autoConnect('publicMessage')
    ... def randomHandler(self, user, channel, message):
    ...     pass
    """
    if isinstance(name_or_func, collections.Callable):
        func = name_or_func
        func.autoConnectToEvent = func.func_name
        return func
    else:
        name = name_or_func
        def inner(func):
            func.autoConnectToEvent = name
        return inner

class IGBotPlugin(IPlugin):
    """
    Identification plugin for Twisted. For now, may
    evolve later.
    """
    pass

class EventListener(object):
    """
    An event listener can register handlers to listen
    to global events put out by the bot.
    """
    def __init__(self, bot):
        self.bot = bot
        self.eventRegistry = {}

    def activate(self):
        self.active = True
        self.bot.listeners.remove(self)

    def deactivate(self):
        """
        Deactivate the event listener by 
        """
        self.active = False
        self.bot.listeners.add(self)

    def connect(self, name, func):
        """
        Connect a function to the named event by registering
        it as a handler for the event.

        Use the autoConnect decorator to call this function
        """
        self.eventRegistry.setdefault(name, []).append(func)
        return func

    def disconnect(self, name, func):
        """
        Disconnect a function from the named event.
        """
        self.eventRegistry.get(name, [func]).remove(func)

    def __getitem__(self, item):
        return self.eventRegistry[item]

    def keys(self):
        return self.eventRegistry.keys()
 
def commandHandler(argspec=['rest'], authLevel=None,
                   needs=[], name=None, Command=Command):
    """
    Handler to handle commands.
    """
    def inner(func):
        command = Command(func, argspec, needs, authLevel, name)
        func.autoCommand = command
        return func
    return inner

class BasePlugin(EventListener):

    class __metaclass__(type):
        implements(IGBotPlugin)
    
    def __init__(self, bot, channel, config):
        super(BasePlugin, self).__init__(bot)
        self.commandRegistry = {}
        self.eventRegistry = {}
        self.channel, self.config = channel, config
        self.connectEvents()
        self.autoConnect()
        self.loadConfiguration(config)
        self.loadCommandConfig(config)

    def loadCommandConfig(self, config):
        self.prefixChar = config.get('PrefixChar', None)
        self.prefixChar = self.bot.config.get('PrefixChar', self.prefixChar)

    def loadConfiguration(self, config):
        pass

    @autoConnect('privateMessage')
    def _command_privateMessage(self, user, msg):
        self.bot.message(user, user, msg)
        self._handleCommand(user, user, msg, addressed=True)

    @autoConnect('publicMessage')
    def _command_publicMessage(self, user, channel, msg):
        self.bot.message(user, channel, msg)
        self._handleCommand(user, channel, msg)

    def _handleCommand(self, user, channel, msg, addressed=False):
        msg = msg.strip()
        if msg.startswith(self.bot.nickname):
            msg = msg[len(self.bot.nickname):].strip()
            if msg[0] in ':,':
                msg = msg[1:].strip()
                addressed = True

        if msg[0] == self.prefixChar:
            msg = msg[1:].strip()
            
        command, _, args = msg.partition(' ')
        func = self.commandRegistry.get(command, None)
        if func:
            log.msg("Command %r found, calling." % (command,))
            func(self.bot, user, channel, msg)
        else:
            log.msg("Command %r not found" % (command,))

    def connectEvents(self):
        pass

    def autoConnect(self):
        for func in self.__dict__.itervalues():
            if getattr(func, "autoConnectToEvent", None):
                self.connect(func.autoConnectToEvent, func)
            if getattr(func, "autoCommand", None):
                self.commandRegistry[func.autoCommand.name] = func.autoCommand
