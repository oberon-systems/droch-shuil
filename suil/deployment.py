import inspect
import logging

from pyinfra.api.exceptions import PyinfraError

from suil.errors import SuilError
from suil.libs import (module_collect_facts, module_get_config, module_get_public, module_run_check, module_run_code,
                       module_run_drift)
from suil.log import OK
from suil.sdk.errors import DeploymentError, Error
from suil.sdk.libs.module import (check_facter, collect_facts, get_config, get_facts, get_public, get_signature,
                                  load_class, load_code, run_check, run_code, run_drift)
from suil.sdk.libs.node import probe_os
from suil.sdk.libs.pyinfra import connect, make_inventory, make_state, read_failures, run_state
from suil.sdk.libs.run import build_directory

log = logging.getLogger(__name__)


class Deployment:

    def __init__(self, settings, directory, force=False, dry_run=False):
        self.settings = settings
        self.directory = directory
        self.workspace = directory.workspace
        self.force = force
        self.dry_run = dry_run
        self.classes = {}

    def run(self) -> None:
        self.load(module for node in self.directory.nodes for module in node.modules)

        for node in self.directory.nodes:
            state, host, probe = self.connect(node)
            node = self.directory.probe(node.name, probe['family'], probe['release'])
            configs, public = self.configs(node)

            try:
                self.node(state, host, node, configs, public)
            finally:
                build_directory({node.name: {**vars(node), 'public': public}}, self.workspace.runs_dir)

    def load(self, modules) -> None:
        """The class of every module on the SDK, its collector checked, so a broken one fails before a connect."""
        for module in modules:
            if module not in self.classes and not self._old(module):
                check_facter(module, self.workspace.modules_dir)
                self.classes[module] = load_class(module, self.workspace.modules_dir)

    def connect(self, node):
        """Connect first, because the OS layer of the hierarchy is the one whose
        variables are not in the data - only the target knows them."""
        inventory = make_inventory({node.name: node.deployment})
        state = connect(make_state(inventory, self.settings.sudo_password))
        host = state.inventory.get_host(node.name)

        try:
            probe = probe_os(host, self.workspace.facts_dir)
        except PyinfraError as error:
            raise DeploymentError(read_failures(state) or str(error)) from error

        return state, host, probe

    def configs(self, node) -> tuple[dict, dict]:
        """The module configs of a node, secrets in plaintext, and the same with every secret a digest.

        A module on the SDK gets the instance of its class instead of its config, None for a meta module."""
        self.load(node.modules)
        configs, public = {}, {}

        for module in node.modules:
            if self._old(module):
                configs[module] = module_get_config(module, node, self.workspace.modules_dir, self.settings.age_key)
                public[module] = module_get_public(module, node, configs[module], self.settings.age_key)
                continue

            config = get_config(module, node, self.workspace.modules_dir, self.settings.age_key)
            configs[module] = self.classes[module](config) if self.classes[module] else None
            public[module] = get_public(config)

        return configs, public

    def node(self, state, host, node, configs, public) -> None:
        # Read before the collection below, which records the current signature.
        signatures = {module: get_facts(node.name, module, self.workspace.facts_dir).get('signature')
                      for module in node.modules}

        self.facts(host, node, configs, public)
        applied = []

        for module in node.modules:
            changed = self.force or signatures[module] != get_signature(module, self.workspace.modules_dir)
            facts = get_facts(node.name, module, self.workspace.facts_dir).get('facts') or {}
            queued = len(state.ops[host])

            if self._old(module):
                module_run_code(state, host, module, configs[module], facts, changed, self.workspace.modules_dir)
            else:
                run_code(state, host, configs[module], facts, changed)

            if len(state.ops[host]) > queued:
                applied.append(module)

        if not applied:
            log.log(OK, f'{node.name}: nothing to apply')
        else:
            run_state(state, dry_run=self.dry_run)

            if self.dry_run:
                log.warning(f'{node.name}: dry run, nothing applied')
                return

            self.facts(host, node, configs, public, only=applied)

        self.check(node, configs)

    def facts(self, host, node, configs, public, only=None) -> None:
        """Read the target. `only` narrows to the modules given."""
        for module in node.modules:
            if only is not None and module not in only:
                continue

            try:
                if self._old(module):
                    module_collect_facts(host, module, public[module], configs[module],
                                         self.workspace.modules_dir, self.workspace.facts_dir)
                else:
                    collect_facts(host, module, public[module], configs[module],
                                  self.workspace.modules_dir, self.workspace.facts_dir)
            except (SuilError, Error):
                log.warning(f'{node.name}: {module} facts not collected')

    def check(self, node, configs) -> None:
        """What the modules find broken, and what still differs from expected(), in the facts after the run."""
        problems = []

        for module in node.modules:
            facts = get_facts(node.name, module, self.workspace.facts_dir).get('facts') or {}

            if self._old(module):
                found = module_run_check(module, configs[module], facts, self.workspace.modules_dir)
                drift = module_run_drift(module, configs[module], facts, self.workspace.modules_dir)
            else:
                found = run_check(configs[module], facts)
                drift = run_drift(configs[module], facts)

            problems += [f'{node.name}, module {module}: {problem}' for problem in found]

            if drift:
                problems.append(f"{node.name}, module {module}: still differs after the run: {', '.join(drift)}")

        if problems:
            raise DeploymentError('not up after the run\n\n' + '\n'.join(problems))

    def _old(self, module: str) -> bool:
        # A module not migrated yet declares deploy() as a free function; it leaves in step 04.16.
        return inspect.isfunction(getattr(load_code(module, self.workspace.modules_dir), 'deploy', None))
