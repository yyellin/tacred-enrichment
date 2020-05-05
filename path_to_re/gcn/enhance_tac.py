"""Enhance TAC

Usage:
  enhance_tac.py ucca_paths ucca_encodings_min_subtree ucca_heads <tupa_module_path>  [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py ucca_heads <tupa_module_path>  [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py ucca_tokens_min_subtree <tupa_module_path>  [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py ucca_encodings_min_subtree <tupa_module_path>  [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py ucca_paths <tupa_module_path>  [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py ud_paths <corenlp_server> <corenlp_port> [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py ucca_paths <tupa_module_path> ud_paths <corenlp_server> <corenlp_port> [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py debug [--input=<input-file>] [--output=<output-file>]
  enhance_tac.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
import sys
import ijson
import jsonlines
from semstr.convert import to_conllu
from conllu import parse as conllu_parse

from docopt import docopt

from path_to_re.internal.core_nlp_client import CoreNlpClient
from path_to_re.internal.dep_graph import Step, DepGraph
from path_to_re.internal.detokenizer import Detokenizer
from path_to_re.internal.link import Link
from path_to_re.internal.sanitize_tacred import SanitizeTacred
from path_to_re.internal.map_tokenization import MapTokenization
from path_to_re.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe
from path_to_re.internal.tupa_parser import TupaParser
from path_to_re.internal.ud_types import UdRepresentationPlaceholder
from path_to_re.internal.ucca_types import is_terminal


def get_ucca_path(parsed_sentence, tac):

    ucca_tokens = [ucca_terminal.text for ucca_terminal in parsed_sentence.terminals]
    token_map = MapTokenization.map_a_to_b(tac['token'], ucca_tokens)

    if tac['subj_start'] not in token_map \
            or tac['subj_end'] not in token_map \
            or tac['obj_start'] not in token_map \
            or tac['obj_end'] not in token_map:
        print('failed to map "tac tokenization" to "ucca tokenization"')
        return None

    ent1_start = token_map[tac['subj_start']][0] + 1
    ent2_start = token_map[tac['obj_start']][0] + 1


    links = parsed_sentence.get_links()

    ent1_start_node_id = parsed_sentence.get_node_id_by_token_id(ent1_start)
    ent1_parent_node_ids = Link.get_parents(links, ent1_start_node_id)
    if len(ent1_parent_node_ids) == 0:
        print('trouble identifying start node for ent1')
        return None
    ent1_parent_node_id = ent1_parent_node_ids[0]

    ent2_start_node_id = parsed_sentence.get_node_id_by_token_id(ent2_start)
    ent2_parent_node_ids = Link.get_parents(links, ent2_start_node_id)
    if len(ent2_parent_node_ids) == 0:
        print('trouble identifying start node for ent2')
        return None
    ent2_parent_node_id = ent2_parent_node_ids[0]

    graph = DepGraph(links, is_terminal)

    steps = graph.get_undirected_steps(ent1_parent_node_id, ent2_parent_node_id)
    steps_representation = Step.get_default_representation(steps)

    return steps_representation

def get_ucca_tokens_min_subtree(parsed_sentence, tac):

    ucca_tokens = [ucca_terminal.text for ucca_terminal in parsed_sentence.terminals]
    token_map = MapTokenization.map_a_to_b(tac['token'], ucca_tokens)

    if tac['subj_start'] not in token_map \
            or tac['subj_end'] not in token_map \
            or tac['obj_start'] not in token_map \
            or tac['obj_end'] not in token_map:
        print('failed to map "tac tokenization" to "ucca tokenization"')
        return None

    ent1_start = token_map[tac['subj_start']][0] + 1
    ent2_start = token_map[tac['obj_start']][0] + 1


    links = parsed_sentence.get_links()

    ent1_start_node_id = parsed_sentence.get_node_id_by_token_id(ent1_start)
    ent1_parent_node_ids = Link.get_parents(links, ent1_start_node_id)
    if len(ent1_parent_node_ids) == 0:
        print('trouble identifying start node for ent1')
        return None
    ent1_parent_node_id = ent1_parent_node_ids[0]

    ent2_start_node_id = parsed_sentence.get_node_id_by_token_id(ent2_start)
    ent2_parent_node_ids = Link.get_parents(links, ent2_start_node_id)
    if len(ent2_parent_node_ids) == 0:
        print('trouble identifying start node for ent2')
        return None
    ent2_parent_node_id = ent2_parent_node_ids[0]

    graph = DepGraph(links, is_terminal)

    def compare_by(terminal_list, one, another):
        return len(terminal_list)

    subtree = graph.get_minimal_subgraph(ent1_parent_node_id, ent2_parent_node_id, compare_by)
    terminals_of_path = subtree.get_terminals()

    terminals_in_path = sorted([int(i.split('.')[1]) - 1 for i in terminals_of_path])

    reverse_token_map = MapTokenization.map_a_to_b(ucca_tokens, tac['token'])
    tac_terminals_in_path = []
    for terminal_in_path in terminals_in_path:
        for tac_index in reverse_token_map[terminal_in_path]:
            tac_terminals_in_path.append(tac_index)

    return tac_terminals_in_path;

def get_ucca_encodings_min_subtree(parsed_sentence, tac):

    ucca_tokens = [ucca_terminal.text for ucca_terminal in parsed_sentence.terminals]
    token_map = MapTokenization.map_a_to_b(tac['token'], ucca_tokens)

    if tac['subj_start'] not in token_map \
            or tac['subj_end'] not in token_map \
            or tac['obj_start'] not in token_map \
            or tac['obj_end'] not in token_map:
        print('failed to map "tac tokenization" to "ucca tokenization"')
        return None

    ent1_start = token_map[tac['subj_start']][0] + 1
    ent2_start = token_map[tac['obj_start']][0] + 1


    links = parsed_sentence.get_links()

    ent1_start_node_id = parsed_sentence.get_node_id_by_token_id(ent1_start)
    ent1_parent_node_ids = Link.get_parents(links, ent1_start_node_id)
    if len(ent1_parent_node_ids) == 0:
        print('trouble identifying start node for ent1')
        return None
    ent1_parent_node_id = ent1_parent_node_ids[0]

    ent2_start_node_id = parsed_sentence.get_node_id_by_token_id(ent2_start)
    ent2_parent_node_ids = Link.get_parents(links, ent2_start_node_id)
    if len(ent2_parent_node_ids) == 0:
        print('trouble identifying start node for ent2')
        return None
    ent2_parent_node_id = ent2_parent_node_ids[0]

    graph = DepGraph(links, is_terminal)

    def compare_by(terminal_list, one, another):
        return len(terminal_list)

    subtree = graph.get_minimal_subgraph(ent1_parent_node_id, ent2_parent_node_id, compare_by)
    terminals_on_path = subtree.get_terminals()

    terminals_on_path = sorted(terminals_on_path, key = lambda t : int(t.split('.')[1]))

    terminals_of_path_to_ucca_encoding = {}
    for terminal_on_path in terminals_on_path:
        token_index = int(terminal_on_path.split('.')[1]) - 1
        steps = subtree.get_undirected_steps(terminal_on_path, subtree.root())
        terminals_of_path_to_ucca_encoding[token_index] = Step.get_dependency_representation(steps[1:])

    reverse_token_map = MapTokenization.map_a_to_b(ucca_tokens, tac['token'])

    tac_terminals_of_path_to_ucca_encoding = {}
    for terminal_in_path, encoding in terminals_of_path_to_ucca_encoding.items():
        for tac_index in reverse_token_map[terminal_in_path]:
            tac_terminals_of_path_to_ucca_encoding[tac_index] = encoding



    return tac_terminals_of_path_to_ucca_encoding;

def get_ucca_heads(parsed_sentence, tac):

    lines_representation = to_conllu(parsed_sentence.native)
    conllu = conllu_parse('\n'.join(lines_representation))

    ucca_tokens = [ucca_terminal.text for ucca_terminal in parsed_sentence.terminals]
    sanitized_tac_tokens = SanitizeTacred.sanitize_tokens(tac['token'])
    reverse_token_map = MapTokenization.map_a_to_b(ucca_tokens, sanitized_tac_tokens)

    #ensure we have coverage over all of tac['token']
    tac_coverage = {tac_token:True for tac_tokens in reverse_token_map.values() for tac_token in tac_tokens}
    if (len(tac_coverage) != len(tac['token'])) or (0 not in tac_coverage) or ((len(tac_coverage)-1) not in tac_coverage):
        print('failed to allign all UCCA and TACRED tokens for UCCA head/dep extraction')
        return (None, None)

    heads = {i: token_info['head'] for i, token_info in enumerate(conllu[0])}
    tac_heads_lookup = {}
    for index, head in heads.items():
        tac_head = reverse_token_map[head-1][0]+1 if head > 0 else 0
        for tac_index in reverse_token_map[index]:
            tac_heads_lookup[tac_index] = tac_head
    tac_heads = [head for key, head in sorted(tac_heads_lookup.items())]

    deps = {i: token_info['deps'] for i, token_info in enumerate(conllu[0])}
    tac_deps_lookup = {}
    for index, deps in deps.items():
        tac_deps = [(dep, reverse_token_map[head-1][0]+1 if head > 0 else 0) for dep,head in deps]
        for tac_index in reverse_token_map[index]:
            tac_deps_lookup[tac_index] = tac_deps
    tac_deps = [deps for key, deps in sorted(tac_deps_lookup.items())]

    return (tac_heads, tac_deps)



def get_ud_path(sentence, tac, core_nlp):
    parsed_sentence = core_nlp.get_deps(sentence)['sentences'][0]

    ud_parse = []
    for parse_dictionary in parsed_sentence['enhancedPlusPlusDependencies']:
        ud_parse.append((
            parse_dictionary['dependent'],
            parse_dictionary['dependentGloss'],
            parse_dictionary['dep'],
            parse_dictionary['governor'],
            parse_dictionary['governorGloss']))

    ud_tokens = [token['originalText'] for token in parsed_sentence['tokens']]

    token_map = MapTokenization.map_a_to_b(tac['token'], ud_tokens)

    if tac['subj_start'] not in token_map \
            or tac['subj_end'] not in token_map \
            or tac['obj_start'] not in token_map \
            or tac['obj_end'] not in token_map:
        print('failed to map "tac tokenization" to "ud tokenization"')
        return None

    ent1_start = token_map[tac['subj_start']][0]
    ent1_end = token_map[tac['subj_end']][-1]

    ent2_start = token_map[tac['obj_start']][0]
    ent2_end = token_map[tac['obj_end']][-1]

    links = UdRepresentationPlaceholder.get_links_from_ud_dep(ud_parse)
    ent1_head = Link.get_head(links, range(ent1_start, ent1_end + 1))
    ent2_head = Link.get_head(links, range(ent2_start, ent2_end + 1))

    graph = DepGraph(links)
    steps = graph.get_undirected_steps(ent1_head, ent2_head)
    steps_representation = Step.get_default_representation(steps)

    return steps_representation


def enhance_tag(input_stream, output_stream, ud_paths, corenlp_server, corenlp_port, ucca_paths, ucca_tokens_min_subtree, ucca_encodings_min_subtrees, ucca_heads, model_prefix):

    json_read = ijson.items(input_stream, 'item')
    detokenizer = Detokenizer()

    with jsonlines.Writer(output_stream) as json_write:

        if ucca_paths or ucca_tokens_min_subtree or ucca_encodings_min_subtrees or ucca_heads:
            parser = TupaParser(model_prefix)

        if ud_paths:
            core_nlp = CoreNlpClient(corenlp_server, corenlp_port, 15000)

        for item in json_read:
            #sentence = detokenizer.detokenize(item['token'])
            sentence = ' '.join(SanitizeTacred.sanitize_tokens(item['token']))

            if ucca_paths or ucca_tokens_min_subtree or ucca_encodings_min_subtrees or ucca_heads:
                parsed_sentence = parser.parse_sentence(sentence)
                if parsed_sentence is None:
                    print('failed to perform UCCA parse')
                    continue
                item['ucca_parse'] = parsed_sentence.serialize()

            if ucca_paths:
                ucca_path = get_ucca_path(parsed_sentence, item)
                if ucca_path is not None:
                    ucca_path_len = len(ucca_path.split(' ')) + 1
                else:
                    ucca_path_len = -1
                item['ucca_path'] = ucca_path
                item['ucca_path_len'] = ucca_path_len

            if ucca_tokens_min_subtree:
                ucca_words_on_path = get_ucca_tokens_min_subtree(parsed_sentence, item)
                item['ucca_words_on_path'] = ucca_words_on_path

            if ucca_encodings_min_subtrees:
                ucca_encodings_min_subtree = get_ucca_encodings_min_subtree(parsed_sentence, item)
                item['ucca_encodings_min_subtree'] = ucca_encodings_min_subtree

            if ucca_heads:
                ucca_heads, ucca_deps = get_ucca_heads(parsed_sentence, item)
                item['ucca_heads'] = ucca_heads
                item['ucca_deps'] = ucca_deps


            if ud_paths:
                ud_path = get_ud_path(sentence, item, core_nlp)
                if ud_path is not None:
                    ud_path_len = len(ud_path.split(' ')) + 1
                else:
                    ud_path = -1

                item['ud_path'] = ud_path
                item['ud_path_len'] = ud_path_len


            json_write.write(item)


if __name__ == "__main__":
    args = docopt(__doc__)

    input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
    output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout

    get_ud_paths = args.get('get_ud_paths', False)
    corenlp_server = args.get('<corenlp_server>', None)
    corelnlp_port = args.get('<corenlp_port>', '-1')
    corelnlp_port = int(corelnlp_port) if corelnlp_port is not None else -1

    ucca_paths = args.get('ucca_paths', False)
    ucca_tokens_min_subtree = args.get('ucca_tokens_min_subtree', False)
    ucca_encodings_min_subtree = args.get('ucca_encodings_min_subtree', False)
    ucca_heads = args.get('ucca_heads', False)
    tupa_module_path = args.get('<tupa_module_path>', None)


    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    enhance_tag(input_stream, output_stream, get_ud_paths, corenlp_server, corelnlp_port, ucca_paths, ucca_tokens_min_subtree, ucca_encodings_min_subtree, ucca_heads, tupa_module_path)


    #assign_ucca_tree(input, output)

