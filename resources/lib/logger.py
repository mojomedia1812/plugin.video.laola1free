# -*- coding: utf-8 -*-

import re

try:
	import xbmc
except ImportError:
	class XbmcFallback:
		LOGDEBUG = 0
		LOGINFO = 1
		LOGNOTICE = 2
		LOGWARNING = 3
		LOGERROR = 4

		def log(self, message, level=0):
			print(message)

	xbmc = XbmcFallback()

LOGDEBUG = getattr(xbmc, 'LOGDEBUG', 0)
LOGINFO = getattr(xbmc, 'LOGINFO', getattr(xbmc, 'LOGNOTICE', 1))
LOGWARNING = getattr(xbmc, 'LOGWARNING', 3)
LOGERROR = getattr(xbmc, 'LOGERROR', 4)

addon_debug_enabled = False


class Counter:
	def __init__(self):
		self.count = -1

	def increment(self, matchObject):
		self.count += 1
		return '{' + str(self.count) + '}'


def info(message, *arguments):
	log(message, arguments, LOGINFO, 'INFO')


def error(message, *arguments):
	log(message, arguments, LOGERROR, 'ERROR')


def notice(message, *arguments):
	log(message, arguments, LOGINFO, 'NOTICE')


def debug(message, *arguments):
	log(message, arguments, LOGDEBUG, 'DEBUG')


def warn(message, *arguments):
	log(message, arguments, LOGWARNING, 'WARNING')


def log(message, arguments, level, label):
	try:
		try:
			message = message.format(*arguments)
		except ValueError:
			c = Counter()
			message = re.compile('\\{\\}').sub(c.increment, message).format(*arguments)

		if not addon_debug_enabled:
			xbmc.log(message, level)
		else:
			xbmc.log(label + ' - ' + message, LOGINFO)

	except Exception:
		print('Logging failed ' + label + ': "' + message + '" args: ' + str(arguments))
