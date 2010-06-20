##
##    Decide - a plugin for pyGBot
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

from random import choice
from pygbot.baseplugin import BasePlugin, commandHandler

class Decide(BasePlugin):
    @commandHandler()
    def decide(self, bot, user, channel, params, message):
        params = params.split()
        while "or" in params:
            params.remove("or")

        while True:
            try:
                n = params.find("and")
            except AttributeError:
                break

            if n == 0:
                params = params[1:]
                continue

            if params[-1] == "and":
                params = params[:-1]
                continue

            params[n-1:n+2] = ' '.join(params[n-1:n+2])

        if params:
            channel.pubout("I choose %s: " % (choice(params),))
