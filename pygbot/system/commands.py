
from pygbot.baseplugin import BasePlugin, commandHandler

class SystemCommands(BasePlugin):
    @commandHandler(['botChannel', 'rest'])
    def do(self, bot, user, channel, params, message):
        channel, action = params
        bot.describe(channel, action)

    @commandHandler(['botChannel', 'rest'])
    def say(self, bot, user, channel, params, message):
        channel, stuff = params
        bot.say(channel, stuff)

    @commandHandler(['anyChannel'])
    def join(self, bot, user, channel, params, message):
        bot.join(params[0])

    @commandHandler()
    def part(self, bot, user, channel, params, message):
        bot.part(params[0] or channel)

    @commandHandler()
    def activate(self, bot, user, channel, params, message):
        channel.plugins[params[0]].activate()

    @commandHandler()
    def deactivate(self, bot, user, channel, params, message):
        channel.plugins[params[0]].deactivate()
