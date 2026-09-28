import logging

from pyinfra.api.exceptions import PyinfraError

from suil.errors import DeploymentError, SuilError
from suil.libs import (module_collect_facts, module_get_config, module_get_facts, module_get_public,
                       module_get_signature, module_run_check, module_run_code, module_run_drift,
                       node_probe_os, pyinfra_connect, pyinfra_make_inventory, pyinfra_make_state,
                       pyinfra_read_failures, pyinfra_run_state, run_build_directory)
from suil.log import OK

log = logging.getLogger(__name__)


class Deployment:

    def __init__(self, settings, directory, force=False, dry_run=False):
        self.settings = settings
        self.directory = directory
        self.workspace = directory.workspace
        self.force = force
        self.dry_run = dry_run

    def run(self) -> None:
        for node in self.directory.nodes:
            state, host, probe = self.connect(node)
            node = self.directory.probe(node.name, probe['family'], probe['release'])
            configs, public = self.configs(node)

            try:
                self.node(state, host, node, configs, public)
            finally:
                run_build_directory({node.name: {**vars(node), 'public': public}}, self.workspace.runs_dir)

    def connect(self, node):
        """Connect first, because the OS layer of the hierarchy is the one whose
        variables are not in the data - only the target knows them."""
        inventory = pyinfra_make_inventory({node.name: node.deployment})
        state = pyinfra_connect(pyinfra_make_state(inventory, self.settings.sudo_password))
        host = state.inventory.get_host(node.name)

        try:
            probe = node_probe_os(host, self.workspace.facts_dir)
        except PyinfraError as error:
            raise DeploymentError(pyinfra_read_failures(state) or str(error)) from error

        return state, host, probe

    def configs(self, node) -> tuple[dict, dict]:
        """The module configs of a node, secrets in plaintext, and the same with every secret a digest."""
        configs = {module: module_get_config(module, node, self.workspace.modules_dir, self.settings.age_key)
                   for module in node.modules}
        public = {module: module_get_public(module, node, configs[module], self.settings.age_key)
                  for module in node.modules}

        return configs, public

    def node(self, state, host, node, configs, public) -> None:
        # Read before the collection below, which records the current signature.
        signatures = {module: module_get_facts(node.name, module, self.workspace.facts_dir).get('signature')
                      for module in node.modules}

        self.facts(host, node, configs, public)
        applied = []

        for module in node.modules:
            changed = self.force or signatures[module] != module_get_signature(module, self.workspace.modules_dir)
            facts = module_get_facts(node.name, module, self.workspace.facts_dir).get('facts') or {}
            queued = len(state.ops[host])

            module_run_code(state, host, module, configs[module], facts, changed, self.workspace.modules_dir)

            if len(state.ops[host]) > queued:
                applied.append(module)

        if not applied:
            log.log(OK, f'{node.name}: nothing to apply')
        else:
            pyinfra_run_state(state, dry_run=self.dry_run)

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
                module_collect_facts(host, module, public[module], configs[module],
                                     self.workspace.modules_dir, self.workspace.facts_dir)
            except SuilError:
                log.warning(f'{node.name}: {module} facts not collected')

    def check(self, node, configs) -> None:
        """What the modules find broken, and what still differs from expected(), in the facts after the run."""
        problems = []

        for module in node.modules:
            facts = module_get_facts(node.name, module, self.workspace.facts_dir).get('facts') or {}
            problems += [f'{node.name}, module {module}: {problem}'
                         for problem in module_run_check(module, configs[module], facts, self.workspace.modules_dir)]

            drift = module_run_drift(module, configs[module], facts, self.workspace.modules_dir)

            if drift:
                problems.append(f"{node.name}, module {module}: still differs after the run: {', '.join(drift)}")

        if problems:
            raise DeploymentError('not up after the run\n\n' + '\n'.join(problems))
