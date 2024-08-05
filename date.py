import pytz
from datetime import datetime


class Date:
	@staticmethod
	def parse(string_date: str, date_format: str ='%d/%m/%Y') -> list[datetime]:  # dd/mm/yyyy || dd/mm/yyyy - dd/mm/yyyy
		return [
			datetime.strptime(date.strip(), date_format)
			for date in string_date.split('-')
		]

	@staticmethod
	def reformat(date: str, from_format: str, to_format: str) -> str:
		parsed_date = datetime.strptime(date, from_format)
		return parsed_date.strftime(to_format)

	@staticmethod
	def local_to_utc(dt: datetime, tz: str) -> datetime:
		local_tz = pytz.timezone(tz)
		local_dt = local_tz.localize(dt)
		return local_dt.astimezone(pytz.utc)

	@staticmethod
	def utc_to_local(dt: datetime, tz: str) -> datetime:
		local_tz = pytz.timezone(tz)
		local_dt = dt.astimezone(local_tz)
		return local_tz.normalize(local_dt)

	@staticmethod
	def format(dates: list[datetime], date_format: str ='%d/%m/%Y') -> str:
		return ' - '.join([
			date.strftime(date_format) for date in dates if date
		])
