# -*- coding: utf-8 -*-


class Settings:
	def __init__(self, addon):
		self.addon = addon

	def get(self, key):
		return self.addon.getSetting(key) or ''

	def set(self, key, value):
		try:
			self.addon.setSetting(key, value or '')
		except AttributeError:
			pass

	def choice(self, key, values, default):
		value = self.get(key)
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
		value = self.get('location')
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

	def username(self):
		return self.get('username').strip()

	def password(self):
		return self.get('password')

	def id_token(self):
		if self.token_username() != self.username():
			return ''
		return self.get('auth_id_token')

	def access_token(self):
		if self.token_username() != self.username():
			return ''
		return self.get('auth_access_token')

	def refresh_token(self):
		if self.token_username() != self.username():
			return ''
		return self.get('auth_refresh_token')

	def token_username(self):
		return self.get('auth_username')

	def set_tokens(self, id_token, access_token, refresh_token, username):
		self.set('auth_id_token', id_token)
		self.set('auth_access_token', access_token)
		self.set('auth_refresh_token', refresh_token)
		self.set('auth_username', username)

	def clear_tokens(self):
		self.set_tokens('', '', '', '')

	def stream_session_id(self):
		if self.token_username() != self.username():
			return ''
		return self.get('auth_stream_session_id')

	def stream_session_start(self):
		if self.token_username() != self.username():
			return ''
		return self.get('auth_stream_session_start')

	def set_stream_session(self, session_id, session_start):
		self.set('auth_stream_session_id', session_id)
		self.set('auth_stream_session_start', session_start)

	def debug(self):
		return self.get('debug') == 'true'

	def livefilter(self):
		livefilters = ['all', 'icehockey', 'tabletennis', 'basketball', 'volleyball', 'beachvolley', 'handball', 'football']
		return self.choice('livefilter', livefilters, 'all')

	def livelimit(self):
		value = self.get('livelimit')
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
		return self.get('htmlstripping') == 'true'
