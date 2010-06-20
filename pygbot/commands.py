
import functools
import shlex

from functools import wraps

parserRegistry   = {}
verifierRegistry = {}

### TODO: optional
def optional(func):
    @wraps(func)
    def inner(default):
        def inner_(*args):
            return func(*args)
        inner_.isOptional = True
        inner_.default = default
        return inner_
    return inner

def parser(func, registry=parserRegistry):
    registry[func] = func
    registry[func.func_name] = func
    registry[func.func_name.lower()] = func
    func.isOptional = False
    func.optional = optional(func)
    return func

def verifier(func, registry=verifierRegistry):
    registry[func] = func
    registry[func.func_name] = func
    if func.func_name.startswith("need"):
        registry[func.func_name[4:]] = func
        registry[func.func_name[4:].lower()] = func
    return func

class CommandError(Exception): pass

def checkAuthLevel(authLevel):
    def inner(message, bot, user, channel):
        if channel.auth[user] < authLevel:
            return CommandError("You do not have sufficient "
                                "privileges for this command.")
    return inner

@verifier
def needPM(message, bot, user, plugin, channel):
    """
    Verifies that the user is
    using a private message.
    """
    if bot.nickname != channel.name:
        return CommandError("This command needs to be private")

@verifier
def needPublic(message, bot, user, plugin, channel):
    """
    Verifies that the user is using
    a public channel the bot is in.
    """
    if bot.nickname != channel.name:
        return CommandError("This command needs to be private")

@parser
def identity(parts, index, message, bot, plugin, user, channel):
    """
    Accepts anything.
    """
    return parts[index]

@parser
def rest(parts, index, message, bot, plugin, user, channel):
    """
    Accepts the rest of the parts.
    """
    return ' '.join(parts[index:])

@parser
def anyChannel(parts, index, message, bot, plugin, user, channel):
    """
    Any channel.
    """
    part = parts[index]
    if part[0] not in bot.supported.getFeature('CHANTYPES'):
        return CommandError("Not a channel")
    return part

@parser
def botChannel(parts, index, message, bot, plugin, user, channel):
    """
    A channel the bot is currently in.
    """
    part = parts[index]
    if bot.channelFactory(bot, part) not in bot.channels:
        return CommandError("I am not in " + channel)
    return part

@parser
def channelUser(parts, index, message, bot, plugin, user, channel):
    """
    A user in the current channel.
    """
    part = parts[index]
    if bot.userFactory(bot, part) not in channel.users:
        return CommandError("User not found")
    return part

@parser
def anyUser(parts, index, message, bot, plugin, user, channel):
    """
    Any user.
    """
    return parts[index]

class Command(object):
    def __init__(self, func, parsers=[], verifiers=[],
                 authLevel=None, name=None):
        self.name = name or func.func_name
        self.func = func
        self.parsers = [parserRegistry.get(p, identity) for p in parsers]
        self.argcount = len(parsers)
        verifiers = [verifierRegistry[p] for p in verifiers]
        if authLevel:
            verifiers.append(checkAuthLevel(authLevel))
        self.verifiers = verifiers

    def verify(self, bot, plugin, user, channel, message):
        return [f(message, bot, plugin, user, channel) for f in self.verifiers if f]

    def parse(self, bot, plugin, user, channel, message):
        parts = shlex.split(message)
        parsers = self.parsers[:]
        return  [f(parts, i, message, bot, plugin, user, channel)
                 for i, f in enumerate(parts)]

    def __call__(self, bot, plugin, user, channel, message):
        if channel == user: # PM
            channel = bot.nickname

        channel = bot.channelFactory(bot, channel)
        user = bot.user(user)

        errors = self.verify(bot, plugin, user, channel, message)
        if errors:
            channel.pubout(str(errors[0]))
            return

        results = self.parse(bot, plugin, user, channel, message)
        errors = [R for R in results if isinstance(R, CommandError)]

        if errors:
            channel.pubout(str(errors[0]))
            return

        # Get our function, but decrease it to a regular
        # function instead of an instance attribute.
        func = self.func
        func = getattr(func, "im_func", func)

        func(plugin, bot, user, channel, results, message)
