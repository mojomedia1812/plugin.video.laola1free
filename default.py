# -*- coding: utf-8 -*-

import sys
from urllib.parse import parse_qs

import xbmcaddon

from resources.lib.handlers import BlockHandler
from resources.lib.handlers import ChannelHandler
from resources.lib.handlers import LiveBlockHandler
from resources.lib.handlers import VideoHandler
from resources.lib.settings import Settings
from resources.lib import logger


def main():
	addonhandle = int(sys.argv[1])
	addonbaseurl = sys.argv[0]

	addon = xbmcaddon.Addon()
	addonname = addon.getAddonInfo('id')

	settings = Settings(addon)

	logger.addon_debug_enabled = settings.debug()
	logger.notice('Debug logging enabled: ' + str(logger.addon_debug_enabled))

	logger.info('Starting addon with {}', sys.argv)
	try:
		logger.info('Python version: {}.{}.{}', sys.version_info[0], sys.version_info[1], sys.version_info[2])
	except Exception:
		logger.warn('Python version info could not be loaded')

	parameters = parse_qs(sys.argv[2][1:])
	request_type = parameters.get('type', ['channel'])[0]

	handler = None
	if request_type == 'channel':
		handler = ChannelHandler(addonhandle, addonname, addonbaseurl, parameters, settings)
	elif request_type == 'live-block':
		handler = LiveBlockHandler(addonhandle, addonname, addonbaseurl, parameters, settings)
	elif request_type == 'block':
		handler = BlockHandler(addonhandle, addonname, addonbaseurl, parameters, settings)
	elif request_type == 'video':
		handler = VideoHandler(addonhandle, addonname, addonbaseurl, parameters, settings)

	if handler is None:
		logger.error('Unknown handler type "{}"', request_type)
	else:
		handler.handle()
		handler.finish()


if __name__ == '__main__':
	main()
