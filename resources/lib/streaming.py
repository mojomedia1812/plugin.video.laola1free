# -*- coding: utf-8 -*-

import re
from datetime import datetime
from urllib.parse import urlencode
from urllib.parse import urljoin

from . import logger
from .net import NetworkError
from .net import get_json
from .net import get_text
from .net import post_json

CONTENT_API = 'https://video.laola1.at/api/v3/contents'
SITE_BASE = 'https://www.laola1.at/de/'


class StreamError(Exception):
	def __init__(self, message):
		super().__init__(message)
		self.message = message


class Stream:
	def __init__(self, url, video_id=None, min_bandwidth=0, max_bandwidth=999999999):
		self.title = None
		self.min_bandwidth = min_bandwidth
		self.max_bandwidth = max_bandwidth

		self.video_id = video_id or self.extract_video_id(url)
		if not self.video_id:
			self.video_id = self.extract_video_id_from_page(url)

		if not self.video_id:
			raise StreamError('Videoplayer not found!')

		logger.debug('Get stream details for content id "{}"', self.video_id)
		content = self.get_content(self.video_id)
		self.title = self.extract_title(content) or self.title
		self.url = self.get_playlist_url(self.video_id, content)
		logger.debug('Playlist url is "{}"', self.url)

	def extract_video_id(self, value):
		if not value:
			return None

		value = str(value)
		if value.isdigit():
			return value

		patterns = [
			r'/contents/(\d+)',
			r'/(?:player|embed)/(\d+)',
			r'(?:video|livestream)_(\d+)',
		]
		for pattern in patterns:
			match = re.search(pattern, value)
			if match:
				return match.group(1)

		return None

	def extract_video_id_from_page(self, url):
		logger.debug('Search video id in page "{}"', url)
		content = get_text(url)
		match = re.search(r'data-video-id=["\'](\d+)["\']', content)
		if match:
			return match.group(1)

		match = re.search(r'/video/player/(\d+)/', content)
		if match:
			return match.group(1)

		title_match = re.search(r'<title>(.+?)</title>', content, re.DOTALL)
		if title_match:
			self.title = re.sub(r'\s+', ' ', title_match.group(1)).strip()

		return None

	def get_content(self, video_id):
		response = get_json('{}/{}'.format(CONTENT_API, video_id))
		return response.get('data', {})

	def extract_title(self, content):
		translations = content.get('editorial', {}).get('translations', {})
		for language in ('de', 'en'):
			title = translations.get(language, {}).get('title')
			if title:
				return title

		return None

	def get_playlist_url(self, video_id, content):
		self.raise_if_not_started(content)

		settings = self.get_player_settings(video_id)
		stream_access = settings.get('streamAccess')
		if not stream_access:
			stream_access = settings.get('streamUrlProviderInfo', {}).get('data', {}).get('streamAccessUrl')

		if not stream_access:
			raise StreamError('Stream access URL could not be loaded.')

		try:
			response = post_json(stream_access, headers={
				'Origin': 'https://www.laola1.at',
				'Referer': SITE_BASE + 'video/player/{}/'.format(video_id)
			})
		except NetworkError as exc:
			if exc.status == 401:
				raise StreamError(self.authorization_error(content))
			raise StreamError('Stream access failed: {}'.format(exc))

		if response.get('status') != 'success':
			raise StreamError(response.get('message') or 'Stream access failed.')

		stream = response.get('data', {}).get('stream')
		if not stream:
			raise StreamError('Stream URL could not be loaded.')

		return stream

	def get_player_settings(self, video_id):
		query = urlencode({
			'portal': 'at',
			'autoplay': 'true',
			'enableProgressBar': 'true',
			'enableTime': 'true',
			'enableSeekForward': 'true',
			'enableSeekBehind': 'true',
			'showTitle': 'true',
			'customDimension14': SITE_BASE + 'video/player/{}/'.format(video_id)
		})
		return get_json('{}/{}/player-settings?{}'.format(CONTENT_API, video_id, query))

	def raise_if_not_started(self, content):
		status = content.get('status', {})
		if status.get('id') not in (1, 2):
			return

		start_time = self.parse_datetime(content.get('startTime'))
		if start_time:
			raise StreamError('Stream not yet started![CR]Stream start: ' + start_time.strftime('%a, %d.%m. %H:%M'))

		raise StreamError('Stream not yet started!')

	def authorization_error(self, content):
		payment = content.get('payment') or {}
		entitlements = payment.get('entitlements') or []
		if entitlements:
			return 'This stream requires a LAOLA1 login or subscription.'

		status = content.get('status', {}).get('name')
		if status:
			return 'Stream is currently not available. Status: {}'.format(status)

		return 'Stream is currently not available.'

	def parse_datetime(self, value):
		if not value:
			return None

		try:
			return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone()
		except ValueError:
			return None

	def get_title(self):
		return self.title

	def get_url(self):
		return self.url

	def get_playlist(self):
		streamurl = self.get_url()
		master = get_text(streamurl)

		playlist = '#EXTM3U\n'
		lines = master.splitlines()

		for index, line in enumerate(lines):
			if not line.startswith('#EXT-X-STREAM-INF'):
				continue

			match = re.search(r'BANDWIDTH=(\d+)', line)
			if not match or index + 1 >= len(lines):
				continue

			bandwidth = int(match.group(1))
			url = lines[index + 1].strip()
			if self.min_bandwidth < bandwidth and bandwidth <= self.max_bandwidth:
				playlist += line + '\n' + urljoin(streamurl, url) + '\n'

		return playlist
