from typing import Callable

from jinja2 import BaseLoader, TemplateNotFound


class TemplateLoader(BaseLoader):
    def __init__(self, templates: dict[str, str]):
        self.templates = templates

    def get_source(self, environment, template: str) -> tuple[str, str, Callable]:
        template_data = self.templates.get(template)
        if template_data is None:
            raise TemplateNotFound(template)
        return template_data, template, lambda: True
