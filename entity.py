from typing   import Callable


from pydantic import BaseModel


class Entity(BaseModel):
	@classmethod
	def _get_decorators(cls) -> dict[str, Callable]:
		decorators = {}
		for name in cls.__dict__:
			if name.startswith('define_'):
				f = getattr(cls, name)
				if callable(f):
					decorators[name[7:]] = f
		return decorators

	@classmethod
	def _decorate_data(cls, **data) -> dict:
		for name, f in cls._get_decorators().items():
			data[name] = f(**data)
		return data


	def __init__(self, /, **data):
		super().__init__(**self._decorate_data(**data))
