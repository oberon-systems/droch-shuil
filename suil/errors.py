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
    message; a SuilError without a traceback, any other with one."""
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
    # A SuilError or an sdk Error has logged itself already.
    if not isinstance(error, (SuilError, Error)):
        log.error(f'{kind.__name__}: {error}',
                  exc_info=None if isinstance(error, KNOWN) else (kind, error, traceback))


class SuilError(Exception):
    """ Base class of every error the runner raises deliberately; it logs itself when made """

    def __init__(self, message: str):
        super().__init__(message)
        log.error(message)


class DirectoryRoleExists(SuilError):
    """ Role Already Registered into Directory """


class DirectoryError(SuilError):
    """ A run was asked for both a role and a node """


class DataError(SuilError):
    """ A data file is missing, unreadable or not the shape a layer must have """


class ModuleError(SuilError):
    """ A module is missing, has no code, or its code cannot be imported """


class ModuleConfigError(SuilError):
    """ A module config failed validation on the control machine """


class ModuleOrderError(SuilError):
    """ The requires graph does not resolve - a cycle or a module that is not there """


class ModuleValidateError(SuilError):
    """ A rendered file was rejected by the checker on the target """


class SecretError(SuilError):
    """ An encrypted value could not be read - no key, wrong key, bad ciphertext """


class NodeProbeError(SuilError):
    """ The OS of a node could not be determined """


class DeploymentError(SuilError):
    """ An operation failed on a target and the run cannot go on """
