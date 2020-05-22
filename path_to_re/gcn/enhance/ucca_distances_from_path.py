from path_to_re.gcn.enhance.ucca_enhancer import UccaEnhancer
from path_to_re.internal.ucca_types import UccaParsedPassage
import itertools
import networkx


class UccaDistancesFromPath(UccaEnhancer):

    def enhance(self, tac, tac_to_ucca, ucca: UccaParsedPassage):

        ucca_tokens = [ucca_terminal.text for ucca_terminal in ucca.terminals]
        sent_len = len(ucca_tokens)

        subj_start = tac_to_ucca[tac['subj_start']][0]
        subj_end = tac_to_ucca[tac['subj_end']][-1]
        subj = list(range(subj_start, subj_end+1))

        obj_start = tac_to_ucca[tac['obj_start']][0]
        obj_end = tac_to_ucca[tac['obj_end']][-1]
        obj = list(range(obj_start, obj_end+1))

        multi_heads = [[int(head) for dep, head in ucca_deps] for ucca_deps in tac['ucca_deps']]

        edges = {(head_id-1, id): True for id in range(sent_len) for head_id in multi_heads[id]}

        extended_edges = edges.copy()
        for edge in itertools.combinations(subj, 2):
            extended_edges[edge] = True
        for edge in itertools.combinations(obj, 2):
            extended_edges[edge] = True

        graph = networkx.Graph(list(extended_edges.keys()))
        try:
            on_path = networkx.shortest_path(graph, source=subj[0], target=obj[0])
        except networkx.NetworkXNoPath:
            print('no path between source and target')
            return {'dist_from_ucca_mh_path': None}


        all_shortest_paths_lengths = {start: targets for start, targets in networkx.shortest_path_length(graph)}

        token_distances = []
        for token_id in range(sent_len):
            distance = 0
            if token_id not in on_path:
                distances_to_path = {target: distance_to_target
                                     for target, distance_to_target in all_shortest_paths_lengths[token_id].items()
                                     if target in on_path}
                distance = min(distances_to_path.values(), default=1e12)
            token_distances.append(distance)

        return {'dist_from_ucca_mh_path': token_distances}


#        json_write.write(tac)

