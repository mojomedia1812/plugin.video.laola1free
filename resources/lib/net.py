# -*- coding: utf-8 -*-

import json
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

USER_AGENT = 'Mozilla/5.0 (Kodi; plugin.video.laola1free)'

DEFAULT_HEADERS = {
	'Accept': '*/*',
	'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
	'User-Agent': USER_AGENT,
}


class NetworkError(Exception):
	def __init__(self, message, status=None, body=None, url=None):
		super().__init__(message)
		self.status = status
		self.body = body
		self.url = url


def request(url, data=None, headers=None, method=None, timeout=30):
	payload = data
	if isinstance(payload, str):
		payload = payload.encode('utf-8')

	request_headers = dict(DEFAULT_HEADERS)
	if headers:
		request_headers.update(headers)

	req = Request(url, data=payload, headers=request_headers, method=method)
	try:
		response = urlopen(req, timeout=timeout)
		try:
			body = response.read()
			encoding = response.headers.get_content_charset() or 'utf-8'
			return body.decode(encoding, 'replace')
		finally:
			response.close()
	except HTTPError as exc:
		body = exc.read().decode('utf-8', 'replace')
		raise NetworkError('HTTP {} {}'.format(exc.code, exc.reason), exc.code, body, url)
	except URLError as exc:
		raise NetworkError(str(exc.reason), None, None, url)


def get_text(url, headers=None):
	return request(url, headers=headers)


def get_json(url, headers=None):
	return json.loads(get_text(url, headers=headers))


def post_json(url, data=b'', headers=None):
	post_headers = {'Accept': 'application/json'}
	if headers:
		post_headers.update(headers)
	return json.loads(request(url, data=data, headers=post_headers))
