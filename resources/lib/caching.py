# -*- coding: utf-8 -*-

import json
import os

from . import logger


class CacheManager:
	def __init__(self, path):
		if not os.path.exists(path):
			os.makedirs(path, exist_ok=True)
		self.path = path

	def clear(self):
		for file in os.listdir(self.path):
			filepath = os.path.join(self.path, file)
			try:
				if os.path.isfile(filepath):
					os.unlink(filepath)
			except Exception as e:
				logger.warn('Failed to clear cache {}', e)

	def get_filepath(self, idParts):
		joined = '-'.join(str(e) for e in idParts)
		if joined:
			joined = '-' + joined
		return os.path.join(self.path, 'cache' + joined + '.json')

	def load(self, idParts):
		idPartsNew = idParts[:-1]
		filepath = self.get_filepath(idPartsNew)

		while not os.path.isfile(filepath) and len(idPartsNew) > 0:
			del idPartsNew[-1]
			filepath = self.get_filepath(idPartsNew)

		if not os.path.isfile(filepath):
			return None

		logger.debug('Read from "{}"', filepath)

		with open(filepath, 'r', encoding='utf-8') as file:
			obj = json.load(file)

		return self.get_child(obj, idParts[len(idPartsNew):])

	def get_child(self, items, idParts):
		logger.debug("id: {}, list: {}", idParts, items)

		if not idParts:
			return items

		if len(items) == 0:
			return None

		try:
			parent = items[idParts[0]]
		except IndexError:
			return None

		if len(idParts) == 1:
			return parent

		if parent and 'children' in parent:
			return self.get_child(parent['children'], idParts[1:])

		return None

	def store(self, obj, parentIdParts=None):
		if parentIdParts is None:
			parentIdParts = []

		filepath = self.get_filepath(parentIdParts)

		with open(filepath, 'w', encoding='utf-8') as file:
			json.dump(obj, file, ensure_ascii=False)
