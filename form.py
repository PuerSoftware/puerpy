import html
import inspect

from collections import OrderedDict
from typing      import Any
from types       import UnionType, NoneType

from pydantic    import BaseModel
from fastapi     import Header, Form as FormField
from loguru      import logger

def is_saving(isSaving: int = Header(...)) -> bool:
    return bool(int(
        isSaving or 0
    ))

def JsonFormField(*args, **kwargs) -> FormField:
    kwargs['media_type'] = 'application/json'
    return FormField(*args, **kwargs)

class FormValidationError(Exception):
    ...

class FormResponse(BaseModel):
    error        : str | None
    errors       : dict[str, str]
    name         : str | None
    data         : dict[str, Any]
    redirect_uri : str | None = None


class Form(BaseModel):
    """
    Form for dynamic field validation
    """
    class _:
        ...

    form_name: str | None = JsonFormField(None)

    def __init__(self, **data):
        self._.name       = data.get('form_name')
        self._.data       = self._escape(data) # escape html for xss prevention
        self._.valid_data = {}
        self._.errors     = OrderedDict()
        self._.error      = None # global form error
    
    def _escape(data: dict[str, Any]) -> dict[str, Any]:
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = html.escape(value)
        return data

    def _is_field_required(self, annotation: UnionType | Any) -> bool:
        if isinstance(annotation, UnionType):
            annotation = annotation.__args__
            return len(annotation) < 2 or annotation[-1] != NoneType
        return True
        

    def _get_validate_method(self, name):
        method_name = f'validate_{name}'
        if hasattr(self, method_name):
            return getattr(self, method_name)

    @property
    def error_count(self) -> int:
        return len(self._.errors)

    @property
    def form_error(self) -> str | None:
        if self._.error:
            return self._.error
        if self.error_count:
            s = 's' if self.error_count > 1 else ''
            return f'This form contains {self.error_count} error{s}'
        return None

    @form_error.setter
    def form_error(self, value: str):
        if not isinstance(value, str):
            raise Exception('Form error must be an instance of str')
        self._.error = value

    @property
    def is_valid(self) -> bool:
        return not bool(self._.errors) and not bool(self._.error)

    @property
    def valid_data(self) -> dict:
        return self._.valid_data

    @property
    def response(self) -> FormResponse:
        return FormResponse(
            error  = self.form_error,
            errors = self._.errors,
            name   = self._.name,
            data   = self._.data
        )

    async def validate(self):
        for field_name, field_info in self.model_fields.items():
            if field_name == 'form_name':
                continue
            value = self._.data.get(field_name)
            if not self.is_valid and (value is None or value == ''):
                break
            if self._is_field_required(field_info.annotation) and (value is None or value == ''):
                self._.errors[field_name] = 'Field is required'
                break
            if method := self._get_validate_method(field_name):
                try:
                    if inspect.iscoroutinefunction(method):
                        self._.valid_data[field_name] = await method(value)
                    else:
                        self._.valid_data[field_name] = method(value)
                except FormValidationError as e:
                    self._.errors[field_name] = str(e)
                except Exception as e:
                    logger.error(f'{self.__class__.__name__}.{field_name}: {e}')
                    self._.errors[field_name] = 'This field contains error'
            else:
                self._.valid_data[field_name] = value
