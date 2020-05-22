from path_to_re.gcn.enhance.ucca_enhancer import UccaEnhancer
from path_to_re.internal.ucca_types import UccaParsedPassage
from path_to_re.internal.dep_graph import Step, DepGraph
from path_to_re.internal.link import Link
from path_to_re.internal.ucca_types import is_terminal


class UccaEncoding(UccaEnhancer):

    def enhance(self, tac, tac_to_ucca, ucca: UccaParsedPassage):

        links = ucca.get_links()
        graph = DepGraph(links, is_terminal)

        terminals_to_ucca_encoding = {}
        for terminal_on_path in ucca.terminals:
            token_index = int(terminal_on_path.node_id.split('.')[1]) - 1
            steps = graph.get_undirected_steps(terminal_on_path.node_id, graph.root())
            terminals_to_ucca_encoding[token_index] = Step.get_dependency_representation(steps[1:]) if len(steps) > 1 else ''

        return {'ucca_encodings':terminals_to_ucca_encoding}


