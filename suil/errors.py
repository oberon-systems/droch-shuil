import functools
import logging
import sys
import threading

from pydantic import ValidationError

from suil.config import Config
from suil.log import log_setup
from suil.sdk.errors import Error

log = logging.getLogger(__name__)

# Foreign errors whose message says all there is: no traceback for them.
KNOWN = (ValidationError,)


def errors_handler(function):
    """An entry point of suil: every error, wherever it comes from, ends it with one
    message; an sdk Error without a traceback, any other with one."""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        # The settings are not read yet, so the color is the model's default until they are.
        log_setup(Config.model_fields['log_color'].default)
        sys.excepthook = _report
        threading.excepthook = lambda hook: _report(hook.exc_type, hook.exc_value, hook.exc_traceback)

        try:
            return function(*args, **kwargs)
        except KeyboardInterrupt:
            log.warning('interrupted')
            raise SystemExit(130)
        except Exception as error:
            _report(type(error), error, error.__traceback__)
            raise SystemExit(1)

    return wrapper


def _report(kind, error, traceback) -> None:
    # An sdk Error has logged itself already.
    if not isinstance(error, Error):
        log.error(f'{kind.__name__}: {error}',
                  exc_info=None if isinstance(error, KNOWN) else (kind, error, traceback))


class DirectoryRoleExists(Error):
    """ Role Already Registered into Directory """


class DirectoryError(Error):
    """ A run was asked for both a role and a node """
