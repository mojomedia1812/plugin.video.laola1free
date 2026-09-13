# -*- coding: utf-8 -*-

import re
from datetime import datetime
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

from . import logger
from .net import get_json

API_BASE = 'https://api.laola1.at/postings/api/v1'
SITE_BASE = 'https://www.laola1.at/de/'
VIDEOS_URL = API_BASE + '/videos'
LIVESTREAMS_URL = API_BASE + '/livestreams'

SPORT_FOLDERS = [
	('Football', 'Fussball', 'resource:icons/soccer.png'),
	('Basketball', 'Basketball', 'resource:icons/basketball.png'),
	('Handball', 'Handball', 'resource:icons/volleyball.png'),
	('Volleyball', 'Volleyball', 'resource:icons/volleyball.png'),
	('Beach volleyball', 'Beachvolleyball', 'resource:icons/volleyball.png'),
	('Ice hockey', 'Eishockey', 'resource:icons/hockey.png'),
	('Tennis', 'Tennis', 'resource:icons/tennis.png'),
	('Motorsport', 'Motorsport', 'resource:icons/motorsport.png'),
]

SPORT_FILTERS = {
	'beachvolleyball': 'beachvolley',
	'beachvolley': 'beachvolley',
	'basketball': 'basketball',
	'eishockey': 'icehockey',
	'football': 'football',
	'fussball': 'football',
	'handball': 'handball',
	'icehockey': 'icehockey',
	'tabletennis': 'tabletennis',
	'tischtennis': 'tabletennis',
	'volleyball': 'volleyball',
}


class Extractor:
	def __init__(self, baseurl, settings):
		self.baseurl = baseurl
		self.settings = settings

	def api_url(self, path, **query):
		if not query:
			return API_BASE + path

		return API_BASE + path + '?' + urlencode(query)

	def get_text(self, item):
		return item.get_text().strip()

	def get_url(self, url):
		return urljoin(self.baseurl, url)

	def get_channels(self):
		channels = [
			{
				'label': 'Live and upcoming',
				'url': LIVESTREAMS_URL,
				'type': 'live-block',
				'image': 'resource:icons/trophy.png'
			},
			{
				'label': 'Latest videos',
				'url': VIDEOS_URL,
				'type': 'block',
				'image': 'DefaultFolder.png'
			}
		]

		for label, search, image in SPORT_FOLDERS:
			channels.append({
				'label': label,
				'url': self.api_url('/videos', search=search),
				'type': 'block',
				'image': image
			})

		return channels

	def get_blocks(self):
		return self.get_videos()

	def get_live_videos(self):
		logger.info('Fetching livestreams from "{}"', self.baseurl)
		payload = get_json(self.baseurl)
		items = payload.get('data', [])
		livelimit = self.settings.livelimit()
		videos = []

		for item in items:
			start = self.parse_datetime(item.get('liveAt') or item.get('publishedAt'))
			if livelimit and start:
				days_from_now = (start.date() - datetime.now(start.tzinfo).date()).days
				if days_from_now >= livelimit:
					continue

			video = self.convert_api_item(item, True)
			if video:
				videos.append(video)

		return videos

	def get_videos(self):
		logger.info('Fetching videos from "{}"', self.baseurl)
		payload = get_json(self.baseurl)
		videos = []

		for item in payload.get('data', []):
			video = self.convert_api_item(item, False)
			if video:
				videos.append(video)

		if payload.get('hasMorePages'):
			videos.append({
				'label': 'More...',
				'url': self.next_page_url(self.baseurl, payload.get('currentPage', 1)),
				'type': 'block'
			})

		return videos

	def convert_api_item(self, item, live_listing):
		video_id = self.extract_video_id(item)
		if not video_id:
			logger.warn('Skipping video without content id: {}', item)
			return None

		title = item.get('title') or 'Untitled'
		video = {
			'label': self.format_label(item, title, live_listing),
			'title': title,
			'url': item.get('link') or (SITE_BASE + 'video/player/{}/'.format(video_id)),
			'video_id': str(video_id),
			'type': 'video',
			'genre': item.get('videoSport') or 'Sports',
			'plot': item.get('description') or ''
		}

		if item.get('image'):
			video['image'] = item['image']

		if item.get('videoLength'):
			video['duration'] = int(item['videoLength'])

		sport = self.normalize_sport(item.get('videoSport') or item.get('videoCategory') or '')
		if sport:
			video['sport'] = sport

		return video

	def extract_video_id(self, item):
		entity_id = item.get('entityId') or ''
		match = re.search(r'_(\d+)$', entity_id)
		if match:
			return match.group(1)

		link = item.get('link') or ''
		match = re.search(r'/(?:player|embed)/(\d+)', link)
		if match:
			return match.group(1)

		return None

	def format_label(self, item, title, live_listing):
		if live_listing and item.get('isLive'):
			return '[COLOR red]LIVE[/COLOR] - ' + title

		date = self.parse_datetime(item.get('liveAt') or item.get('publishedAt'))
		if not date:
			return title

		if live_listing:
			return '[B]' + date.strftime('%a, %d.%m. %H:%M') + '[/B] - ' + title

		return '[B]' + date.strftime('%d.%m.%Y') + '[/B] - ' + title

	def parse_datetime(self, value):
		if not value:
			return None

		try:
			return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone()
		except ValueError:
			logger.warn('Could not parse date "{}"', value)
			return None

	def normalize_sport(self, value):
		key = value.lower().replace('ß', 'ss')
		key = re.sub(r'[^a-z]', '', key)
		return SPORT_FILTERS.get(key)

	def next_page_url(self, url, current_page):
		parts = urlsplit(url)
		query = dict(parse_qsl(parts.query))
		query['page'] = str(int(query.get('page', current_page)) + 1)
		return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
