import html
import inspect

from collections    import OrderedDict
from typing         import Any
from types          import UnionType, NoneType

from pydantic       import BaseModel
from fastapi        import Header
from fastapi.params import Form as FastApiFormFieldParam
from loguru         import logger

def is_saving(isSaving: int = Header(...)) -> bool:
    return bool(int(
        isSaving or 0
    ))


class FormFieldParam(FastApiFormFieldParam):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = kwargs.get('required', True)

def FormField(*args, **kwargs) -> FormFieldParam:
    return FormFieldParam(*args, **kwargs)

def JsonFormField(*args, **kwargs) -> FormFieldParam:
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

    form_name: str | None = JsonFormField(None, required=False)

    def __init__(self, **data):
        super().__init__(**data)
        self._name       = data.get('form_name')
        self._data       = self._escape(self._vaidate_types(data)) # escape html for xss prevention
        self._valid_data = {}
        self._errors     = OrderedDict()
        self._error      = None # global form error
    
    def _escape(self, data: dict[str, Any]) -> dict[str, Any]:
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = html.escape(value)
        return data
    
    def _vaidate_types(self, data: dict[str, Any]) -> dict[str, Any]:
        for k, v in data.items():
            if info := self.model_fields.get(k):
                if v is not None:
                    _type = None
                    if isinstance(info.annotation, UnionType):
                        _type = info.annotation.__args__[0]
                    else:
                        _type = info.annotation
                    try:
                        data[k] = _type(v)
                    except TypeError:
                        raise FormValidationError(f'Mismatched type for field "{k}"')
        return data

    def _get_validate_method(self, name):
        method_name = f'validate_{name}'
        if hasattr(self, method_name):
            return getattr(self, method_name)

    @property
    def error_count(self) -> int:
        return len(self._errors)

    @property
    def form_error(self) -> str | None:
        if self._error:
            return self._error
        if self.error_count:
            s = 's' if self.error_count > 1 else ''
            return f'This form contains {self.error_count} error{s}'
        return None

    @form_error.setter
    def form_error(self, value: str):
        if not isinstance(value, str):
            raise Exception('Form error must be an instance of str')
        self._error = value

    @property
    def is_valid(self) -> bool:
        return not bool(self._errors) and not bool(self._error)

    @property
    def valid_data(self) -> dict:
        return self._valid_data

    @property
    def response(self) -> FormResponse:
        return FormResponse(
            error  = self.form_error,
            errors = self._errors,
            name   = self._name,
            data   = self._data
        )

    async def validate(self):
        for field_name, field_info in self.model_fields.items():
            if field_name == 'form_name':
                continue
            value = self._data.get(field_name)
            if not self.is_valid and (value is None or value == ''):
                break
            if field_info.required and (value is None or value == ''):
                self._errors[field_name] = 'Field is required'
                break
            if field_info.required or (not field_info.required and value is not None):
                if method := self._get_validate_method(field_name):
                    try:
                        if inspect.iscoroutinefunction(method):
                            self._valid_data[field_name] = await method(value)
                        else:
                            self._valid_data[field_name] = method(value)
                    except FormValidationError as e:
                        self._errors[field_name] = str(e)
                    except Exception as e:
                        logger.error(f'{self.__class__.__name__}.{field_name}: {e}')
                        self._errors[field_name] = 'This field contains error'
                else:
                    self._valid_data[field_name] = value
