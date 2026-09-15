from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Tuple
from pydantic import BaseModel
from suil import tui
from suil.errors import ModuleError, ModuleValidateError
from suil.models import SuilConfig
from suil.libs import (
    deep_merge,
    module_collect_files,
    module_diff_configs,
    module_diff_names,
    module_file_digest,
    module_file_needs_write,
    module_get_defaults,
    module_get_files,
    module_validate_file,
)


class ModuleInteractionMixin:
    """Standardized interaction methods via suil.tui (used by both TUI and CLI)."""
    def info(self, msg: str): tui.info(msg)
    def ok(self, msg: str): tui.ok(msg)
    def warn(self, msg: str): tui.warn(msg)
    def bad(self, msg: str): tui.bad(msg)


class ModuleUtilsMixin:
    """Standardized access to Suil utilities."""
    @staticmethod
    def deep_merge(target: Dict, source: Dict) -> Dict:
        """Recursively merge source into target."""
        return deep_merge(target, source)

    @staticmethod
    def diff_configs(expected: Dict, facts: Dict, path: Tuple = ()) -> Dict:
        """Compute recursive diff of expected vs actual facts."""
        return module_diff_configs(expected, facts, path)

    @staticmethod
    def diff_names(diff: Dict, field: str) -> set:
        """Extract specific field names from a diff."""
        return module_diff_names(diff, field)

    @staticmethod
    def validate_file(host: Any, content: str, command: str) -> None:
        """Validate file content using a command on the host."""
        return module_validate_file(host, content, command)

    @staticmethod
    def get_defaults(module: str, modules_dir: Any) -> Dict:
        """Get default configurations for a module."""
        return module_get_defaults(module, modules_dir)

    @staticmethod
    def get_files(module: str, modules_dir: Any) -> list:
        """List files available to the module."""
        return module_get_files(module, modules_dir)

    @staticmethod
    def collect_files(module: str, modules_dir: Any) -> Dict:
        """Collect and return file contents."""
        return module_collect_files(module, modules_dir)

    @staticmethod
    def file_digest(content: str) -> str:
        """Compute SHA256 digest of file content."""
        return module_file_digest(content)

    @staticmethod
    def file_needs_write(current_content: str, new_content: str) -> bool:
        """Check if file needs update."""
        return module_file_needs_write(current_content, new_content)

    # Exceptions & Config
    ModuleError = ModuleError
    ModuleError.__doc__ = "Base error for module-related failures."

    ModuleValidateError = ModuleValidateError
    ModuleValidateError.__doc__ = "Raised when file validation fails."

    SuilConfig = SuilConfig
    SuilConfig.__doc__ = "Base configuration model for all modules."


@dataclass(frozen=True)
class ModuleInterface(ABC, ModuleInteractionMixin, ModuleUtilsMixin):
    """
    Standard interface for all modules.
    Must be implemented by modules to ensure standardization.
    """

    @abstractmethod
    def deploy(self, config: BaseModel, facts: Dict[str, Any]) -> None:
        """Apply the configuration based on the provided facts."""
        pass

    @abstractmethod
    def expected(self, config: BaseModel) -> Dict[str, Any]:
        """Return the expected state based on the configuration."""
        pass


@dataclass(frozen=True)
class FactCollectorInterface(ABC, ModuleInteractionMixin, ModuleUtilsMixin):
    """
    Standard interface for all fact collectors.
    Must be implemented to standardize how facts are gathered.
    """

    @abstractmethod
    def collect(self, config: BaseModel) -> Dict[str, Any]:
        """Collect and return facts based on the configuration."""
        pass
