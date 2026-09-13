# -*- coding: utf-8 -*-


class Settings:
	def __init__(self, addon):
		self.addon = addon

	def choice(self, key, values, default):
		value = self.addon.getSetting(key)
		if value in values:
			return value

		try:
			return values[int(value)]
		except (TypeError, ValueError, IndexError):
			return default

	def language(self):
		languages = ['en', 'de']
		return self.choice('language', languages, 'de')

	def location(self):
		value = self.addon.getSetting('location')
		if value == 'de':
			return 'de'

		if value in ('all', 'at', 'int', ''):
			return 'all'

		legacy_locations = ['int', 'de', 'at']
		try:
			location = legacy_locations[int(value)]
			if location == 'de':
				return 'de'
		except (TypeError, ValueError, IndexError):
			pass

		return 'all'

	def debug(self):
		return self.addon.getSetting('debug') == 'true'

	def livefilter(self):
		livefilters = ['all', 'icehockey', 'tabletennis', 'basketball', 'volleyball', 'beachvolley', 'handball', 'football']
		return self.choice('livefilter', livefilters, 'all')

	def livelimit(self):
		value = self.addon.getSetting('livelimit')
		if value in ('none', ''):
			return None

		if value in ('3', '7', '14'):
			return int(value)

		livelimits = [None, 3, 7, 14]
		try:
			return livelimits[int(value)]
		except (TypeError, ValueError, IndexError):
			return None

	def htmlstripping(self):
		return self.addon.getSetting('htmlstripping') == 'true'
