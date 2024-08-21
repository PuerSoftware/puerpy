from typing import Any


class Reflection:
	@staticmethod
	def subclasses(parent: Any) -> set:
		children = set()
		parents  = [parent]
		while parents:
			parent = parents.pop()
			for child in parent.__subclasses__():
				if child not in children:
					children.add(child)
					parents.append(child)
		return children
	