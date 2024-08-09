import html
import inspect

from collections    import OrderedDict
from datetime       import datetime
from typing         import Any
from types          import UnionType

from pydantic       import BaseModel
from fastapi.params import Form as FastApiFormFieldParam#
from loguru         import logger


class FormFieldParam(FastApiFormFieldParam):
    def __init__(self, *args, **kwargs):
        self._is_required = kwargs.pop('is_required', True)
        super().__init__(*args, **kwargs)

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
    form_name    : str | None
    is_saving    : bool
    is_saved     : bool
    data         : dict[str, Any]
    redirect_uri : str | None = None


class Form(BaseModel):
    """
    Form for dynamic field validation
    """

    form_name: str  | None = JsonFormField(None, is_required=False)
    is_saving: bool | None = JsonFormField(None, is_required=True)

    def __init__(self, **data):
        super().__init__(**data)
        self._name       = data.pop('form_name', None)
        self._is_saving  = data.pop('is_saving')
        self._data       = self._escape(self._vaidate_types(data)) # escape html for xss prevention
        self._valid_data = {}
        self._errors     = OrderedDict()
        self._error      = None # global form error
    
    def _escape(self, data: dict[str, Any]) -> dict[str, Any]:
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = html.escape(value)
        return data
    
    def _cast(self, _type: Any, v: Any) -> Any:
        if _type == datetime:
            v = datetime.fromisoformat(v)
        if not isinstance(v, _type):
            v = _type(v)
        return v


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
                        data[k] = self._cast(_type, v)

                    except TypeError:
                        raise FormValidationError(f'Mismatched type for field "{k}", got {type(v)}, expected {_type}')
        return data

    def _get_validate_method(self, name):
        method_name = f'validate_{name}'
        if hasattr(self, method_name):
            return getattr(self, method_name)
    
    def _has_field(self, field) -> bool:
        return field in self.model_fields

    def _is_field_required(self, field) -> bool:
        return self.model_fields[field]._is_required

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
    def data(self) -> dict:
        return self._data
    
    @data.setter
    def data(self, data: dict):
        self._data = self._escape(self._vaidate_types(data))

    @property
    def valid_data(self) -> dict:
        return self._valid_data

    @property
    def is_saved(self) -> bool:
        return self._is_saving and self.is_valid

    @property
    def response(self) -> FormResponse:
        return FormResponse(
            error     = self.form_error,
            errors    = self._errors,
            form_name = self._name,
            is_saving = self._is_saving,
            is_saved  = self.is_saved,
            data      = self._data
        )
    
    async def validate(self):
        for field, value in self._data.items():

            if not self.is_valid and (value is None or value == ''):
                break
            if not self._has_field(field):
                self._error = f'Unknown field "{field}"'
                break
            if self._is_field_required(field) and (value is None or value == ''):
                self._errors[field] = 'Field is required'
                break

            if method := self._get_validate_method(field):
                try:
                    if inspect.iscoroutinefunction(method):
                        self._valid_data[field] = await method(value)
                    else:
                        self._valid_data[field] = method(value)
                except FormValidationError as e:
                    self._errors[field] = str(e)
                    continue
                except Exception as e:
                    logger.exception(f'{self.__class__.__name__}.{field}: {e}')
                    self._errors[field] = 'This field contains error'
                    continue
            else:    
                self._valid_data[field] = value
