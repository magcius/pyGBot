##
##    DnDStatsRoll - a plugin for pyGBot
##    Copyright (C) 2008 Morgan Lokhorst-Blight, Alex Soborov
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

import random
import re

from pygbot.baseplugin import BasePlugin, handleCommand

class DnDStatsRoll(BasePlugin):
    __plugintype__ = "active"
    
    def __init__(self, bot, options):
        BasePlugin.__init__(self, bot, options)
        self.activeGame = False
        self.output = True
        self.modbreak = re.compile('([\+\-\*\/%^].*)')

    @handleCommand()
    def rollstats(self, bot, plugin, user, channel, parts, message):
        """ Roll up a standard 6x4d6 (drop lowest) D&D Stats roll."""
        rolls = [[random.randint(1,6) for i in range(0,4)] for j in range(0,6)]

        # Drop lowest of each 4d6 set and sum to produce 6 stat values
        stats = [sum(sorted(x)[1:]) for x in rolls] 
 
        return rolls, stats
