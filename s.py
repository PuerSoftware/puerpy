class String:
	@staticmethod
	def screaming_snake_to_camel(s: str) -> str:
		return ''.join([
			w.capitalize() for w in s.split('_')
		])

	@staticmethod
	def camel_to_screaming_snake(s: str) -> str:
		result = [s[0].upper()]
		for char in s[1:]:
			if char.isupper():
				result.append('_')
				result.append(char)
			else:
				result.append(char.upper())
		return ''.join(result)

	@staticmethod
	def to_kebab(s: str) -> str:
		return s.lower().replace(' ', '-')
