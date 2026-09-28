import logging

log = logging.getLogger(__name__)


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
