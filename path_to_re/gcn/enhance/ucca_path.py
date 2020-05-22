from path_to_re.gcn.enhance.ucca_enhancer import UccaEnhancer
from path_to_re.internal.ucca_types import UccaParsedPassage
from path_to_re.internal.dep_graph import Step, DepGraph
from path_to_re.internal.link import Link
from path_to_re.internal.ucca_types import is_terminal


class UccaPath(UccaEnhancer):

    def enhance(self, tac, tac_to_ucca, ucca: UccaParsedPassage):

        ent1_start = tac_to_ucca[tac['subj_start']][0] + 1
        ent1_end = tac_to_ucca[tac['subj_end']][-1] + 1
        ent2_start = tac_to_ucca[tac['obj_start']][0] + 1
        ent2_end = tac_to_ucca[tac['obj_end']][-1] + 1

        links = ucca.get_links()

        for ent1_index in range(ent1_start, ent1_end+1):
            ent1_start_node_id = ucca.get_node_id_by_token_id(ent1_start)
            ent1_parent_node_ids = Link.get_parents(links, ent1_start_node_id)
            if len(ent1_parent_node_ids) > 0:
                break
        if len(ent1_parent_node_ids) == 0:
            print('trouble identifying parent node for subj')
            return {'ucca_path': None, 'ucca_path_len': -1}
        ent1_parent_node_id = ent1_parent_node_ids[0]


        for ent2_index in range(ent2_start, ent2_end+1):
            ent2_start_node_id = ucca.get_node_id_by_token_id(ent2_start)
            ent2_parent_node_ids = Link.get_parents(links, ent2_start_node_id)
            if len(ent2_parent_node_ids) > 0:
                break
        if len(ent2_parent_node_ids) == 0:
            print('trouble identifying parent node for obj')
            return {'ucca_path': None, 'ucca_path_len': -1}
        ent2_parent_node_id = ent2_parent_node_ids[0]

        graph = DepGraph(links, is_terminal)

        steps = graph.get_undirected_steps(ent1_parent_node_id, ent2_parent_node_id)
        ucca_path = Step.get_default_representation(steps)
        ucca_path_len = len(ucca_path.split(' '))+1 if ucca_path else -1

        return {'ucca_path': ucca_path, 'ucca_path_len': ucca_path_len}
