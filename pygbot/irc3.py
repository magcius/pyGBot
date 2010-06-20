from twisted.words.protocols import irc
from twisted.internet import reactor, defer, task
from twisted.python import log, failure
import collections
import functools
import datetime
import operator
import time
import uuid
import os

class IRCError(Exception):
    pass

class NicknameInUseError(IRCError):
    pass

class ErroneousNicknameError(IRCError):
    pass

class CouldNotChangeNicknameError(IRCError):
    pass

class BannedFromChannelError(IRCError):
    pass

class InviteOnlyChannelError(IRCError):
    pass

class WrongChannelKeyError(IRCError):
    pass

class ChannelIsFullError(IRCError):
    pass

class NotOnChannelError(IRCError):
    pass

class NoNicknameGivenError(IRCError):
    pass

def random_identifier():
    return str(uuid.uuid4())

class IRCTarget(object):
    def __init__(self, protocol, target):
        self.protocol, self.target = protocol, target
        self.comparison_key = target.lower(), protocol
    
    def __eq__(self, other):
        return self.comparison_key == other.comparison_key
    
    def __hash__(self):
        return hash(self.comparison_key)
    
    def __getattr__(self, attr):
        return self.make_partial(getattr(self.protocol, attr))
    
    def __repr__(self):
        return '<%s(%s), targeting %r at %#x>' % (
            type(self).__name__, self.target, self.protocol, id(self))
        

class Channel(IRCTarget):
    def __init__(self, protocol, target):
        self.users = set()
        super(Channel, self).__init__(protocol, target)

    def make_partial(self, meth):
        return lambda *a, **kw: meth(channel=self, *a, **kw)

class User(IRCTarget):
    def __init__(self, protocol, wholeUser):
        self.nick, _, userhost = wholeUser.partition('!')
        self.user, _, self.host = userhost.partition('@')
        super(User, self).__init__(protocol, self.nick)

    def make_partial(self, meth):
        return lambda *a, **kw: meth(user=self, *a, **kw)

def applyToResult(applied):
    def deco(func):
        def wrap(*a, **kw):
            return func(*a, **kw).addCallback(applied)
        return wrap
    return deco

def commandGenerator(func):
    def wrap(self, *a, **kw):
        return self._issueCommand(lambda: func(self, *a, **kw))
    return wrap

class _CmdGen_Return(BaseException):
    def __init__(self, value):
        self.value = value

def returnValue(val):
    raise _CmdGen_Return(val)

def not_disjoint(s1, s2):
    return any(True for v in s2 if v in s1)

class IRCClient(irc.IRCClient):
    channelFactory = Channel
    userFactory = User
    
    def channel(self, channel):
        if isinstance(channel, Channel): return channel
        ret = self.channelFactory(self, channel)
        return self.channels.setdefault(ret, ret)
    
    def user(self, wholeUser):
        if isinstance(wholeUser, User): return wholeUser
        ret = self.userFactory(self, wholeUser)
        return self.users.setdefault(ret, ret)
    
    def from_source(self, source):
        prefixes = self.supported.getFeature('CHANTYPES')
        if source.startswith(prefixes):
            ret = self.channel(source)
        else:
            ret = self.user(source)
        return ret
    
    def __init__(self):
        self.channels = {}
        self.users = {}
        self._ping_data = {}
        self.pursue_looper = task.LoopingCall(self._isonCheck)
        self.pursuing = False
        self._current_command = None
        self._command_queue = collections.deque()
        self._result = {}
    
    def _issueCommand(self, issuer):
        d = defer.Deferred()
        self._command_queue.append((issuer, d))
        self._pumpQueue()
        return d
    
    def _pumpQueue(self, forcibly=False):
        if self._current_command is not None and not forcibly:
            return
        if self._command_queue:
            issuer, d = self._command_queue.popleft()
            self._current_command = issuer(), d
            self._stepGenerator()
        else:
            self._current_command = None
    
    def _stepGenerator(self, result=None, failure=None):
        issuer, d = self._current_command
        waitingOn = None
        try:
            if failure is not None:
                waitingOn = failure.throwExceptionIntoGenerator(issuer)
            else:
                waitingOn = issuer.send(result)
        except StopIteration:
            d.callback(None)
        except _CmdGen_Return, e:
            d.callback(e.value)
        except:
            d.errback()
        finally:
            self._waitingOn = waitingOn
            if waitingOn is None:
                self._pumpQueue(True)
    
    def _partFinished(self, **parts):
        assert not_disjoint(self._waitingOn, parts)
        self._stepGenerator(parts)
    
    def _partFailed(self, f=None, *parts):
        assert not_disjoint(self._waitingOn, parts)
        if not isinstance(f, failure.Failure):
            f = failure.Failure(f)
        self._stepGenerator(failure=f)
    
    # Try to reclaim a nickname if we were forced into using an alternate 
    # nickname by someone else.
    # XXX: This is currently broken. Should be fixed soon.
    pursueDesiredNick = True
    isonCheckInterval = 30
    
    def irc_ERR_NICKNAMEINUSE(self, prefix, params):
        self._partFailed(NicknameInUseError(params[-1]), 'selfnick')
    
    def irc_ERR_ERRONEOUSNICKNAME(self, prefix, params):
        self._partFailed(ErroneousNicknameError(params[-1]), 'selfnick')
    
    def irc_RPL_WELCOME(self, prefix, params):
        self._registered = True
        self._partFinished(selfnick=self._attemptedNick)
        self.signedOn()
    
    def irc_NICK(self, prefix, params):
        user = self.user(prefix)
        if user == self.user(self.nickname):
            self._partFinished(selfnick=params[0])
        else:
            self.userRenamed(user, self.userFactory(params[0]))
            user._nick = params[0]
    
    @commandGenerator
    def setNick(self, nickname):
        self._desiredNick = nickname
        while True:
            irc.IRCClient.setNick(self, nickname)
            try:
                received = yield set(['selfnick'])
            except NicknameInUseError:
                nickname = self.alterCollidedNick(nickname)
            except ErroneousNicknameError:
                nickname = self.erroneousNickFallback
            else:
                break
            if nickname is None:
                raise CouldNotChangeNicknameError()
        self.nickname = nickname
        returnValue(received['selfnick'])
    
    def nickChanged(self, nickname):
        irc.IRCClient.nickChanged(self, nickname)
        self._pursueCheck()
    
    def _pursueCheck(self):
        if not self.pursueDesiredNick:
            return
        if self.pursuing:
            if self.nickname == self._desiredNick:
                self.pursuing = False
                self.pursue_looper.stop()
        else:
            if self.nickname != self._desiredNick:
                self.pursuing = True
                self.pursue_looper.start(self.isonCheckInterval)
    
    @defer.inlineCallbacks
    def _isonCheck(self):
        if not (yield self.ison(self._desiredNick)):
            self.setNick(self._desiredNick)
    
    # Ping the server to make sure that we haven't been silently disconnected.
    serverPingInterval = 60
    disconnectOnLatencyThreshold = 120
    ping_looper = None
    
    def signedOn(self):
        self._pursueCheck()
        if self.serverPingInterval is not None:
            self.ping_looper = task.LoopingCall(self._pingServer)
            self.ping_looper.start(self.serverPingInterval)
    
    @defer.inlineCallbacks
    def _pingServer(self):
        try:
            yield self.ping(timeout=self.disconnectOnLatencyThreshold)
        except defer.TimeoutError:
            self.transport.loseConnection()
    
    def connectionLost(self, reason):
        if self.ping_looper is not None:
            self.ping_looper.stop()
    
    # XXX: Servers also send a message containing who set the topic and when.
    # I should be grabbing that too.
    @commandGenerator
    def topic(self, channel, topic=None):
        irc.IRCClient.topic(self, channel, topic)
        received = yield set(['topic', 'notopic'])
        returnValue(received['topic'])
    
    def irc_RPL_TOPIC(self, prefix, params):
        self._partFinished(topic=params[-1])
    
    def irc_RPL_NOTOPIC(self, prefix, params):
        self._partFinished(topic='', notopic=True)
    
    def irc_RPL_TOPICWHOTIME(self, prefix, params):
        channel = self.channel(params[1])
        setby = self.user(params[2])
        when = datetime.datetime.fromtimestamp(int(params[3]))
        channel.topic_setat = setby, when
    
    @commandGenerator
    def names(self, channel):
        assert ',' not in channel
        self._result['names'] = set()
        self.sendLine('NAMES %s' % channel)
        received = yield set(['names'])
        returnValue(received['names'])
    
    def irc_RPL_NAMREPLY(self, prefix, params):
        nickPrefixes = ''.join(mode for mode, _ in 
            self.supported.getFeature('PREFIX').itervalues())
        nicks = [self.user(nick.lstrip(nickPrefixes)) 
            for nick in params[-1].split()]
        self._result['names'].update(nicks)
    
    def irc_RPL_ENDOFNAMES(self, prefix, params):
        self._partFinished(names=self._result.pop('names'))
    
    @commandGenerator
    def join(self, channel, key=None):
        assert ',' not in channel
        self._result['names'] = set()
        irc.IRCClient.join(self, channel, key)
        waitingOn = set(['joined', 'topic', 'names'])
        sentExtraTopic = False
        channelobj = self.channel(channel)
        while waitingOn:
            received = yield waitingOn
            if 'joined' in received and 'topic' in waitingOn:
                self.sendLine('TOPIC %s' % channel)
                sentExtraTopic = True
                waitingOn.add('notopic')
            if 'topic' in received:
                if sentExtraTopic and 'notopic' not in received:
                    del received['topic']
                    waitingOn.discard('notopic')
                    sentExtraTopic = False
                else:
                    channelobj.topic = received['topic']
            if 'names' in received:
                channelobj.users = received['names']
            waitingOn.difference_update(received)
        returnValue(channelobj)
    
    def irc_JOIN(self, prefix, params):
        user = self.user(prefix)
        channel = self.channel(params[-1])
        if user == self.user(self.nickname):
            self._partFinished(joined=channel)
        else:
            channel.users.add(user)
            self.userJoined(user, channel)
    
    def irc_ERR_BANNEDFROMCHAN(self, prefix, params):
        self._partFailed(BannedFromChannelError(params[-1]), 'joined')
    
    def irc_ERR_INVITEONLYCHAN(self, prefix, params):
        self._partFailed(InviteOnlyChannelError(params[-1]), 'joined')
    
    def irc_ERR_BADCHANNELKEY(self, prefix, params):
        self._partFailed(WrongChannelKeyError(params[-1]), 'joined')
    
    def irc_ERR_CHANNELISFULL(self, prefix, params):
        self._partfiled(ChannelIsFullError(params[-1]), 'joined')
    
    @commandGenerator
    def part(self, channel):
        assert ',' not in channel
        irc.IRCClient.part(self, channel)
        yield set(['parted'])
    
    leave = part
    
    def irc_PART(self, prefix, params):
        user = self.user(prefix)
        channel = self.channel(params[-1])
        if user == self.user(self.nickname):
            self._partFinished(parted=channel)
        else:
            channel.users.add(user)
            self.userLeft(user, channel)
    
    def irc_ERR_NOTONCHANNEL(self, prefix, params):
        self._partFailed(NotOnChannelError(params[-1]), 
            'parted', 'topic', 'invite', 'kick', 'mode')
    
    @commandGenerator
    def banlist(self, channel):
        self._result['bans'] = []
        irc.IRCClient.mode(self, channel, True, 'b')
        received = yield set(['bans'])
        returnValue(received['bans'])
    
    def irc_RPL_BANLIST(self, prefix, params):
        self._result['bans'].append(params[2])
    
    def irc_RPL_ENDOFBANLIST(self, prefix, params):
        self._partFinished(bans=self._result.pop('bans'))
    
    @commandGenerator
    def whois(self, nick, server=None):
        self._result['whois'] = {}
        irc.IRCClient.whois(self, nick, server)
        received = yield set(['whois'])
        returnValue(received['whois'])
    
    def irc_RPL_WHOISUSER(self, prefix, params):
        self._result['whois']['user'] = params[2], params[3], params[5]
    
    def irc_RPL_WHOISSERVER(self, prefix, params):
        self._result['whois']['server'] = params[2], params[3]
    
    def irc_RPL_WHOISOPERATOR(self, prefix, params):
        self._result['whois']['operator'] = True
    
    def irc_RPL_WHOISIDLE(self, prefix, params):
        self._result['whois']['idle'] = int(params[2])
    
    def irc_RPL_WHOISCHANNELS(self, prefix, params):
        chanPrefixes = ''.join(mode for mode, _ in 
            self.supported.getFeature('PREFIX').itervalues())
        self._result['whois'].setdefault('channels', set()).update(
            self.channel(chan.lstrip(chanPrefixes)) 
            for chan in params[-1].split())
    
    def irc_RPL_WHOISSPECIAL(self, prefix, params):
        self._result['whois'].setdefault('special', []).append(params[-1])
    
    def irc_RPL_ENDOFWHOIS(self, prefix, params):
        self._partFinished(whois=self._result.pop('whois'))
    
    def irc_ERR_NONICKNAMEGIVEN(self, prefix, params):
        self._partFailed(NoNicknameGivenError(params[-1]), 'whois')
    
    # Some clients don't always uppercase CTCP queries. That really doesn't
    # make much difference.
    def ctcpQuery(self, user, channel, messages):
        messages = [(a.upper(), b) for a, b in messages]
        irc.IRCClient.ctcpQuery(self, user, channel, messages)
    
    def irc_INVITE(self, prefix, params):
        self.invited(self.user(prefix), self.channel(params[1]))
    
    def invited(self, inviter, channel):
        pass
    
    def _pingTimeout(self, key):
        _, d, _ = self._ping_data.pop(key)
        defer.timeout(d)
    
    def _pingSuccess(self, key):
        startTime, d, timeoutCall = self._ping_data.pop(key)
        latency = time.time() - startTime
        if timeoutCall is not None:
            timeoutCall.cancel()
        d.callback(latency)
    
    def ping(self, user=None, data=None, timeout=None):
        d = defer.Deferred()
        if data is None:
            data = random_identifier()
        if user is None:
            self.sendLine('PING %s' % data)
        else:
            self.ctcpMakeQuery(user, [('PING', data)])
        if timeout is not None:
            timeoutCall = reactor.callLater(timeout, 
                self._pingTimeout, (user, data))
        else:
            timeoutCall = None
        self._ping_data[user, data] = time.time(), d, timeoutCall
        return d
    
    def irc_PONG(self, prefix, params):
        self._pingSuccess((None, params[-1]))
    
    def ctcpReply_PING(self, user, channel, data):
        user = self.user(user)
        self._pingSuccess((user.nick, data))
    
    def ison(self, *nicks):
        def _doIson():
            self.sendLine('ISON %s' % ' '.join(nicks))
        return self._issueCommand(_doIson, 'ison')
    
    def irc_RPL_ISON(self, prefix, params):
        self._result['ison'] = [self.user(nick) for nick in params[-1].split()]
        self._partFinished('ison')
    
    def privmsg(self, user, channel, message):
        user = self.user(user)
        if channel == self.nickname:
            user.messageReceived(user, message)
            self.privateMessage(user, message)
        else:
            channel = self.channel(channel)
            channel.messageReceived(user, message)
            self.channelMessage(channel, user, message)

    def privateMessage(self, user, message):
        pass
    
    def channelMessage(self, channel, user, message):
        pass

extra_numeric = dict(
    RPL_WHOISSPECIAL='320',
    RPL_TOPICWHOTIME='333',
)
irc.symbolic_to_numeric.update(extra_numeric)
irc.numeric_to_symbolic.update((v, k) for k, v in extra_numeric.iteritems())
