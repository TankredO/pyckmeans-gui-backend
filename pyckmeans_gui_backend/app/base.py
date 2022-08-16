import json
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union
from functools import wraps
from enum import Enum

import tornado.web
import tornado.escape
from tornado.web import _ARG_DEFAULT, _ArgDefaultMarker


class APIResponseJSONEncoder(json.JSONEncoder):
    @staticmethod
    def encode_api_error(api_error: Optional['APIError']) -> Optional[Dict[str, str]]:
        if api_error is None:
            return None
        res: Dict[str, Any] = {
            'type': api_error.type.name,
            'message': api_error.message,
        }
        if isinstance(api_error, MissingParameterAPIError):
            res['parameter_name'] = api_error.parameter_name
        elif isinstance(api_error, MissingParametersAPIError):
            res['parameter_names'] = api_error.parameter_names
        return res

    def encode_data(self, data: Any):
        if data is None:
            return None
        elif isinstance(data, str):
            return data
        elif isinstance(data, int):
            return data
        elif isinstance(data, float):
            return data
        elif isinstance(data, dict):
            res1: Dict[str, Any] = {}
            for k, v in data.items():
                res1[k] = self.encode_data(v)
            return res1
        elif isinstance(data, list) or isinstance(data, tuple):
            res2: List[Any] = []
            for entry in data:
                res2.append(self.encode_data(entry))
            return res2
        else:
            return super().default(data)

    def default(self, obj: Any):
        if isinstance(obj, APIResponse):
            return {
                'data': self.encode_data(obj.data),
                'error': self.encode_api_error(obj.error),
            }

        return super().default(obj)


class APIErrorType(Enum):
    MISSING_TOKEN = 0
    INVALID_TOKEN = 1
    MISSING_PARAMETER = 2
    INVALID_CREDENTIALS = 3
    MISSING_AUTHENTICATION = 4
    FILE_NOT_FOUND = 5
    RUNTIME_ERROR = 6


class APIError:
    def __init__(self, error_type: APIErrorType, error_message: str):
        self.type = error_type
        self.message = error_message


class MissingTokenAPIError(APIError):
    def __init__(self):
        super().__init__(APIErrorType.MISSING_TOKEN, 'Missing authentication token.')


class InvalidTokenAPIError(APIError):
    def __init__(self):
        super().__init__(APIErrorType.INVALID_TOKEN, 'Invalid authentication token.')


class MissingParameterAPIError(APIError):
    def __init__(self, parameter_name: str):
        self.parameter_name = parameter_name
        super().__init__(
            APIErrorType.MISSING_PARAMETER,
            f'Missing required parameter "{parameter_name}"',
        )


class MissingParametersAPIError(APIError):
    def __init__(self, parameter_names: Iterable[str]):
        self.parameter_names = list(parameter_names)
        parameters_str = ", ".join([f'"{p}"' for p in parameter_names])
        super().__init__(
            APIErrorType.MISSING_PARAMETER,
            f'Missing required parameters {parameters_str}',
        )


class InvalidCredentialsAPIError(APIError):
    def __init__(self):
        super().__init__(APIErrorType.INVALID_CREDENTIALS, 'Invalid credentials.')


class MissingAuthenticationAPIError(APIError):
    def __init__(self):
        super().__init__(APIErrorType.MISSING_AUTHENTICATION, 'Missing authentication.')


class APIResponse:
    def __init__(self, data: Any = None, error: Optional[APIError] = None):
        self.data = data
        self.error = error

    def as_json(self) -> Dict[str, Any]:
        return APIResponseJSONEncoder().default(self)

    def as_json_str(self) -> str:
        return json.dumps(self, cls=APIResponseJSONEncoder)


class BaseHandler(tornado.web.RequestHandler):
    def __init__(
        self,
        application: tornado.web.Application,
        request: tornado.httputil.HTTPServerRequest,
        **kwargs: Any,
    ) -> None:
        super().__init__(application, request, **kwargs)

        self._json: Union[Dict[str, Any], List[Any], None] = None

    def get_argument_from_anywhere(
        self,
        arg_name: str,
        default: Union[str, None, _ArgDefaultMarker] = _ARG_DEFAULT,
    ) -> Union[str, None]:
        arg: Union[str, None, _ArgDefaultMarker] = _ARG_DEFAULT

        # try to get from JSON body
        try:
            arg = self.get_json_argument(arg_name)
        except tornado.web.MissingArgumentError:
            pass
        except json.decoder.JSONDecodeError:
            pass

        # try to get from form body
        if arg is _ARG_DEFAULT:
            try:
                arg = self.get_body_argument(arg_name)
            except tornado.web.MissingArgumentError:
                pass

        # try to get from query params
        if arg is _ARG_DEFAULT:
            try:
                arg = self.get_argument(arg_name)
            except tornado.web.MissingArgumentError:
                pass

        if arg is _ARG_DEFAULT:
            arg = default

        # check via isinstance because of mypy
        if isinstance(arg, _ArgDefaultMarker):
            raise tornado.web.MissingArgumentError(arg_name=arg_name)

        return arg

    def get_json_argument(
        self,
        arg_name: str,
        default: Union[str, None, _ArgDefaultMarker] = _ARG_DEFAULT,
    ):
        json = self.json
        if isinstance(json, list):
            return default
        return json.get(arg_name, default)

    @property
    def json(self) -> Union[Dict[str, Any], List[Any]]:
        if self._json is None:
            self._json = tornado.escape.json_decode(self.request.body)
        return self._json


def require_arguments(argument_names=Iterable[str]):
    def decorator(fn):
        @wraps(fn)
        def wrapped(self: BaseHandler, *args, **kwargs):
            missing = []
            for arg_name in argument_names:
                try:
                    arg_val = self.get_argument_from_anywhere(arg_name)
                except tornado.web.MissingArgumentError:
                    missing.append(arg_name)

            if len(missing) > 0:
                api_res = APIResponse(
                    data=None, error=MissingParametersAPIError(missing)
                )
                self.set_status(422)
                self.set_header('Content-Type', 'application/json')
                self.write(api_res.as_json_str())
                return

            return fn(self, *args, **kwargs)

        return wrapped

    return decorator


def with_json_response(fn):
    @wraps(fn)
    def wrapped(self: tornado.web.RequestHandler, *args, **kwargs):
        self.set_header('Content-Type', 'application/json')

        return fn(self, *args, **kwargs)

    return wrapped
