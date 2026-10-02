import logging

log = logging.getLogger(__name__)


class Error(Exception):
    """ Base class of every error the SDK raises deliberately; it logs itself when made """

    def __init__(self, message: str):
        super().__init__(message)
        log.error(message)


class DataError(Error):
    """ A data file is missing, unreadable or not the shape a layer must have """


class ModuleError(Error):
    """ A module is missing, has no code, or its code cannot be imported """


class ModuleConfigError(Error):
    """ A module config failed validation on the control machine """


class ModuleOrderError(Error):
    """ The requires graph does not resolve - a cycle or a module that is not there """


class ModuleValidateError(Error):
    """ A rendered file was rejected by the checker on the target """


class SecretError(Error):
    """ An encrypted value could not be read - no key, wrong key, bad ciphertext """


class NodeProbeError(Error):
    """ The OS of a node could not be determined """


class DeploymentError(Error):
    """ An operation failed on a target and the run cannot go on """
