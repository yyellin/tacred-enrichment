from tacred_enrichment.gcn.enhance.ucca_enhancer import UccaEnhancer
from tacred_enrichment.internal.ucca_types import UccaParsedPassage
from tacred_enrichment.internal.dep_graph import Step, DepGraph
from tacred_enrichment.internal.link import Link
from tacred_enrichment.internal.ucca_types import is_terminal


class UccaEncodingMinSubtree(UccaEnhancer):

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
            return {'ucca_encodings_min_subtree': None,}
        ent1_parent_node_id = ent1_parent_node_ids[0]

        for ent2_index in range(ent2_start, ent2_end+1):
            ent2_start_node_id = ucca.get_node_id_by_token_id(ent2_start)
            ent2_parent_node_ids = Link.get_parents(links, ent2_start_node_id)
            if len(ent2_parent_node_ids) > 0:
                break
        if len(ent2_parent_node_ids) == 0:
            print('trouble identifying parent node for obj')
            return {'ucca_encodings_min_subtree': None,}
        ent2_parent_node_id = ent2_parent_node_ids[0]


        graph = DepGraph(links, is_terminal)

        def compare_by(terminal_list, one, another):
            return len(terminal_list)

        subtree = graph.get_minimal_subgraph(ent1_parent_node_id, ent2_parent_node_id, compare_by)
        terminals_on_path = subtree.get_terminals()

        terminals_on_path = sorted(terminals_on_path, key=lambda t: int(t.split('.')[1]))

        terminals_of_path_to_ucca_encoding = {}
        for terminal_on_path in terminals_on_path:
            token_index = int(terminal_on_path.split('.')[1]) - 1
            steps = subtree.get_undirected_steps(terminal_on_path, subtree.root())
            terminals_of_path_to_ucca_encoding[token_index] = Step.get_dependency_representation(steps[1:])

        return {'ucca_encodings_min_subtree':terminals_of_path_to_ucca_encoding}


