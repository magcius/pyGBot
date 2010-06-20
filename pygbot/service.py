
from __future__ import with_statement

from optparse import OptionParser

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.application import internet, service
from twisted.application.service import IServiceMaker

from pygbot import core, conf

class GBotOptions(usage.Options):
    optParameters = [['config', 'c', conf.default_config]]

    def __init__(self):
        usage.Options.__init__(self)
        self['network'] = ['default']
        self.networkChanged = False

    def opt_network(self, v):
        if self.networkChanged:
            self['network'].append(v)
        else:
            self['network'] = [v]

class GBotServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "gbot"
    description = "An irc bot!"
    options = GBotOptions

    def makeService(self, options):
        app = service.Application('pygbot')
        serv = service.IServiceCollection(app)

        conf.load_config(options['config'])
        networkroot = conf.config['Networks']

        for network in options['network']:
            networkcfg = networkroot.get(network, networkroot['default'])
            factory = core.GBotIrcFactory()
            factory.config = networkcfg
            factory.network = network

            internet.TCPClient(networkcfg['Host'], networkcfg['Port'],
                               factory).setServiceParent(serv)
        return serv
