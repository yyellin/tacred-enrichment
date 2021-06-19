"""ucca_distances_from_path

Usage:
  ucca_distances_from_path.py [--lines] [--input=<input-file>] [--output=<output-file>]
  ucca_distances_from_path.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
from docopt import docopt
import sys
import itertools
import ijson
import jsonlines
import networkx
from tacred_enrichment.internal.ucca_types import UccaParsedPassage


args = docopt(__doc__)

input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout
lines = True if args['--lines'] else False

reader = jsonlines.Reader(input_stream) if lines else ijson.items(input_stream, 'item')

with jsonlines.Writer(output_stream) as json_write:
    for item in reader:

        item['ucca_encodings_min_subtree'] = None

        parsed_sentence = UccaParsedPassage.from_serialization(item['ucca_parse'])
        tac_to_ucca = {int(key): val for key, val in item['tac_to_ucca'].items()}
        sent_len = len(item['ucca_tokens'])

        subj_start = tac_to_ucca[item['subj_start']][0]
        subj_end = tac_to_ucca[item['subj_end']][-1]
        subj = list(range(subj_start, subj_end+1))

        obj_start = tac_to_ucca[item['obj_start']][0]
        obj_end = tac_to_ucca[item['obj_end']][-1]
        obj = list(range(obj_start, obj_end+1))

        heads = [int(x) for x in item['ucca_heads']]
        multi_heads = [[int(head) for dep, head in ucca_deps] for ucca_deps in item['ucca_deps']]

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
            print('shit')
            continue

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

        item['dist_from_ucca_mh_path'] = token_distances

        json_write.write(item)



