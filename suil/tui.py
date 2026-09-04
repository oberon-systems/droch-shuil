import questionary
from suil.config import cfg
from suil.libs import roles_collect, role_get_nodes, node_get_role, hierarchy_load

def roles_select() -> list[str]:

    answer = []

    if roles := roles_collect(cfg.roles_dir):
        answer = questionary.checkbox(
            'Please select roles for a list for run deployment:\n',
            list(roles),
        ).ask()
    return answer

def main():

    questionary.print('\n=== Balor Suil: an infrastructure manager ===\n\n')
    roles = roles_select()

    for role in roles:
        nodes = role_get_nodes(role, cfg.nodes_dir)

    print(nodes)

    for node in nodes:
        print(node_get_role(node,cfg.nodes_dir))


    hierarch = hierarchy_load(cfg.hierarchy_file)
    print(hierarch)
    # todo: run deploy
