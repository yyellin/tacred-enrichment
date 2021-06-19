"""ucca_encodings_min_subtree

Usage:
  ucca_encodings_min_subtree.py [--lines] [--input=<input-file>] [--output=<output-file>]
  ucca_encodings_min_subtree.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
from docopt import docopt
import sys
import ijson
import jsonlines
from tacred_enrichment.internal.ucca_types import UccaParsedPassage
from tacred_enrichment.internal.link import Link
from tacred_enrichment.internal.ucca_types import is_terminal
from tacred_enrichment.internal.dep_graph import Step, DepGraph




args = docopt(__doc__)

input_stream = open(args['--input'], encoding='utf-8') if args['--input'] else sys.stdin
output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] else sys.stdout
lines = True if args['--lines'] else False

reader = jsonlines.Reader(input_stream) if lines else ijson.items(input_stream, 'item')

with jsonlines.Writer(output_stream) as json_write:
    for item in reader:

        item['ucca_encodings_min_subtree'] = None

        parsed_sentence = UccaParsedPassage.from_serialization(item['ucca_parse'])
        tac_to_ucca = { int(key):val for key, val in item['tac_to_ucca'].items() }

        subj_start = tac_to_ucca[item['subj_start']][0] + 1
        obj_start = tac_to_ucca[item['obj_start']][0] + 1

        links = parsed_sentence.get_links()

        subj_start_node_id = parsed_sentence.get_node_id_by_token_id(subj_start)
        subj_parent_node_ids = Link.get_parents(links, subj_start_node_id)
        if len(subj_parent_node_ids) == 0:
            print('trouble identifying start node for subj')
            json_write.write(item)
            continue
        ent1_parent_node_id = subj_parent_node_ids[0]

        obj_start_node_id = parsed_sentence.get_node_id_by_token_id(obj_start)
        obj_parent_node_ids = Link.get_parents(links, obj_start_node_id)
        if len(obj_parent_node_ids) == 0:
            print('trouble identifying start node for ent2')
            json_write.write(item)
            continue
        ent2_parent_node_id = obj_parent_node_ids[0]

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

        item['ucca_encodings_min_subtree'] = terminals_of_path_to_ucca_encoding

        json_write.write(item)



