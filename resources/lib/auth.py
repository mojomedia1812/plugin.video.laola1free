# -*- coding: utf-8 -*-

import base64
import json
import time
from urllib.parse import urlencode

from . import logger
from .net import NetworkError
from .net import post_json

COGNITO_CLIENT_ID = 'qne5505nsusb56k4bmjjfdbev'
COGNITO_ENDPOINT = 'https://cognito-idp.eu-central-1.amazonaws.com/'
POSTINGS_API = 'https://api.laola1.at/postings/api/v1'


class AuthError(Exception):
	pass


class LaolaAuth:
	def __init__(self, settings):
		self.settings = settings

	def is_configured(self):
		return bool(self.settings.username() and self.settings.password())

	def get_id_token(self, force_login=False):
		if not self.is_configured():
			raise AuthError('Please enter your LAOLA1 login details in the add-on settings.')

		if not force_login:
			id_token = self.settings.id_token()
			if self.is_token_valid(id_token):
				return id_token

			refresh_token = self.settings.refresh_token()
			if refresh_token:
				try:
					return self.refresh(refresh_token)
				except AuthError as exc:
					logger.warn('LAOLA1 token refresh failed: {}', exc)
					self.settings.clear_tokens()

		return self.login()

	def login(self):
		response = self.cognito('InitiateAuth', {
			'AuthFlow': 'USER_PASSWORD_AUTH',
			'ClientId': COGNITO_CLIENT_ID,
			'AuthParameters': {
				'USERNAME': self.settings.username(),
				'PASSWORD': self.settings.password(),
			},
		})
		return self.store_authentication_result(response, keep_refresh=False)

	def refresh(self, refresh_token):
		response = self.cognito('InitiateAuth', {
			'AuthFlow': 'REFRESH_TOKEN_AUTH',
			'ClientId': COGNITO_CLIENT_ID,
			'AuthParameters': {
				'REFRESH_TOKEN': refresh_token,
			},
		})
		return self.store_authentication_result(response, keep_refresh=True)

	def cognito(self, target, payload):
		try:
			return post_json(COGNITO_ENDPOINT, data=payload, headers={
				'Content-Type': 'application/x-amz-json-1.1',
				'X-Amz-Target': 'AWSCognitoIdentityProviderService.' + target,
			})
		except NetworkError as exc:
			raise AuthError(self.network_error_message(exc, 'LAOLA1 login failed.'))

	def store_authentication_result(self, response, keep_refresh):
		challenge = response.get('ChallengeName')
		if challenge:
			raise AuthError('LAOLA1 login requires an additional verification step: {}'.format(challenge))

		result = response.get('AuthenticationResult') or {}
		id_token = result.get('IdToken') or ''
		if not id_token:
			raise AuthError('LAOLA1 login did not return a usable session.')

		refresh_token = result.get('RefreshToken')
		if keep_refresh and not refresh_token:
			refresh_token = self.settings.refresh_token()

		self.settings.set_tokens(
			id_token,
			result.get('AccessToken') or '',
			refresh_token or '',
			self.settings.username()
		)
		return id_token

	def get_stream_access_token(self, video_id):
		for force_login in (False, True):
			id_token = self.get_id_token(force_login)
			try:
				access = self.request_stream_access(video_id, id_token)
			except NetworkError as exc:
				if exc.status == 401 and not force_login:
					self.settings.clear_tokens()
					continue
				if exc.status == 403:
					return None
				raise AuthError(self.network_error_message(exc, 'LAOLA1 package access failed.'))

			token = access.get('streamAccessToken')
			if token and access.get('rateLimit') is not False:
				self.check_stream_session(id_token)
			return token

		return None

	def request_stream_access(self, video_id, id_token):
		response = post_json('{}/ext/cleeng/{}/access'.format(POSTINGS_API, video_id), headers={
			'Authorization': 'Bearer ' + id_token,
		})
		data = response.get('data') or {}
		if data.get('success') is False:
			return {}

		return data

	def check_stream_session(self, id_token):
		session_start = self.settings.stream_session_start()
		if not session_start:
			session_start = str(int(time.time()))

		try:
			response = post_json('{}/stream-session'.format(POSTINGS_API), data={
				'sessionId': self.settings.stream_session_id(),
				'sessionStart': int(session_start),
			}, headers={
				'Authorization': 'Bearer ' + id_token,
				'Content-Type': 'application/json',
			})
		except NetworkError as exc:
			logger.warn('LAOLA1 stream session check failed: {}', self.network_error_message(exc, str(exc)))
			return

		data = response.get('data') or {}
		if data.get('sessionId'):
			self.settings.set_stream_session(data.get('sessionId'), session_start)

		if data.get('success') is False:
			raise AuthError('This LAOLA1 account is already streaming on another device.')

	def is_token_valid(self, token):
		payload = self.decode_jwt_payload(token)
		expires = payload.get('exp')
		return bool(expires and time.time() < expires - 60)

	def decode_jwt_payload(self, token):
		if not token or not isinstance(token, str):
			return {}

		parts = token.split('.')
		if len(parts) != 3:
			return {}

		try:
			payload = parts[1].replace('-', '+').replace('_', '/')
			payload += '=' * ((4 - len(payload) % 4) % 4)
			return json.loads(base64.b64decode(payload).decode('utf-8'))
		except Exception:
			return {}

	def network_error_message(self, error, fallback):
		try:
			payload = json.loads(error.body or '{}')
		except ValueError:
			payload = {}

		return payload.get('message') or fallback


def append_query(url, parameters):
	separator = '&' if '?' in url else '?'
	return url + separator + urlencode(parameters)
