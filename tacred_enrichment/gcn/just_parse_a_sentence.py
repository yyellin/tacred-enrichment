from internal.dep_graph import DepGraph, Step
from internal.link import Link
from internal.tupa_parser import TupaParser
from tacred_enrichment.gcn.enhance.ucca_enhancer import UccaEnhancer
from tacred_enrichment.internal.ucca_types import UccaParsedPassage
from semstr.convert import to_conllu
from conllu import parse as conllu_parse

sentence = 'After graduation Johnny transitioned to full-time research'
sentence = 'The Jerusalem Foundation, a charity founded by Kollek 40 years ago, said he died of natural causes.'

parser = TupaParser(r'C:\Users\JYellin\re_1\tupa\models\bert_multilingual_layers_4_layers_pooling_weighted_align_sum')

[parsed_sentence] = parser.parse_sentences([sentence])

# lines_representation = to_conllu(parsed_sentence.native)
# conllu = conllu_parse('\n'.join(lines_representation))
#
# ucca_heads = [token_info['head'] for i, token_info in enumerate(conllu[0])]
# ucca_deps = [token_info['deps'] for i, token_info in enumerate(conllu[0])]

def is_terminal(index):
    return index.startswith('0.')

ent1_start = 1
ent1_end = 3
ent2_start = 8
ent2_end = 8

links = parsed_sentence.get_links()

for ent1_index in range(ent1_start, ent1_end + 1):
    ent1_start_node_id = parsed_sentence.get_node_id_by_token_id(ent1_start)
    ent1_parent_node_ids = Link.get_parents(links, ent1_start_node_id)
    if len(ent1_parent_node_ids) > 0:
        break
if len(ent1_parent_node_ids) == 0:
    print('trouble identifying parent node for subj')
    exit(1)
ent1_parent_node_id = ent1_parent_node_ids[0]

for ent2_index in range(ent2_start, ent2_end + 1):
    ent2_start_node_id = parsed_sentence.get_node_id_by_token_id(ent2_start)
    ent2_parent_node_ids = Link.get_parents(links, ent2_start_node_id)
    if len(ent2_parent_node_ids) > 0:
        break
if len(ent2_parent_node_ids) == 0:
    print('trouble identifying parent node for obj')
    exit(1)
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

#return {'ucca_encodings_min_subtree': terminals_of_path_to_ucca_encoding}

wait_here = True