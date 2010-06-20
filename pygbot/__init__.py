
name = "pyGBot"
description = "an IRC bot, using Twisted and txirc3."

from twisted.plugin import pluginPackagePaths
__path__.extend(pluginPackagePaths(__name__))
__all__ = []
