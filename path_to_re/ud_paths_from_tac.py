import argparse
import csv
import sys

import ijson

from path_to_re.internal.dep_graph import Step, DepGraph
from path_to_re.internal.detokenizer import Detokenizer
from path_to_re.internal.link import Link
from path_to_re.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe
from path_to_re.internal.sync_tac_tags import SyncTacTags
from path_to_re.internal.map_tokenization import MapTokenization
from path_to_re.internal.ud_types import UdRepresentationPlaceholder
from path_to_re.internal.core_nlp_client import CoreNlpClient





def ud_paths_from_tac(input_stream, output_stream, corenlp_server):
    json_stream = ijson.items(input_stream, 'item')
    detokenizer = Detokenizer()
    core_nlp = CoreNlpClient(corenlp_server, 9000, 15000)
    csv_writer = csv.writer(output_stream)
    csv_writer.writerow(['id', 'docid', 'tokens', 'relation', 'path', 'type1', 'type2'])


    for item in json_stream:

        relation = item['relation']
        #if 'no_relation' == relation:
        #    continue

        tac_tokens = item['token']
        sentence = detokenizer.detokenize(tac_tokens)

        # we can access definitely access 'sentences' if 'all_i_ever_wanted' returned without error
        # and as we're only parsing one sentence at a time, we can access [0] for sure. I hope.
        parsed_sentence = core_nlp.get_deps(sentence)['sentences'][0]

        ud_parse = []
        for parse_dictionary in parsed_sentence['enhancedPlusPlusDependencies']:
            ud_parse.append((
                parse_dictionary['dependent'],
                parse_dictionary['dependentGloss'],
                parse_dictionary['dep'],
                parse_dictionary['governor'],
                parse_dictionary['governorGloss']))

        ud_tokens = [token['word'] for token in parsed_sentence['tokens']]

        # tac_tokens_lookup = {
        #     'subj_start': item['subj_start'],
        #     'subj_end': item['subj_end'],
        #     'obj_start': item['obj_start'],
        #     'obj_end': item['obj_end']
        # }
        # ud_token_lookup = SyncTacTags.b_lookup_to_a_lookup(ud_tokens, tac_tokens, tac_tokens_lookup)
        #
        # if (len(ud_token_lookup) != len(tac_tokens_lookup)):
        #     print('were in trouble')
        #     continue
        #
        # ent1_start = ud_token_lookup['subj_start'] + 1
        # ent1_end = ud_token_lookup['subj_end'] + 1
        #
        # ent2_start = ud_token_lookup['obj_start'] + 1
        # ent2_end = ud_token_lookup['obj_end'] + 1

        token_map = MapTokenization.map_a_to_b(tac_tokens, ud_tokens)

        if  item['subj_start'] not in token_map \
            or item['subj_end'] not in token_map \
            or item['obj_start'] not in token_map \
            or item['obj_end'] not in token_map:
            print('failed to map "tac tokenization" to "ud tokenization"')


        ent1_start = token_map[item['subj_start']][0]
        ent1_end = token_map[item['subj_end']][-1]

        ent2_start = token_map[item['obj_start']][0]
        ent2_end = token_map[item['obj_end']][-1]


        links = UdRepresentationPlaceholder.get_links_from_ud_dep(ud_parse)
        ent1_head = Link.get_head(links, range(ent1_start, ent1_end + 1))
        ent2_head = Link.get_head(links, range(ent2_start, ent2_end + 1))

        graph = DepGraph(links)
        steps = graph.get_undirected_steps(ent1_head, ent2_head)
        steps_representation = Step.get_default_representation(steps)

        csv_writer.writerow(
            [item['id'],
             item['docid'],
             ud_tokens,
             relation,
             steps_representation,
             item['subj_type'],
             item['obj_type']])

        wait_here = True


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='ud_paths_from_tac',
        description="receive a TACRED json file and produce a list of UD paths per relation")

    arg_parser.add_argument(
        '--input',
        action='store',
        metavar='input-file',
        help='When provided input will be read from this file rather than from standard input')

    arg_parser.add_argument(
        '--output',
        action='store',
        metavar='output-file',
        help='The comma-separated field output file (if not provided output will be sent to std output)')

    arg_parser.add_argument(
        '--corenlp-server',
        default='localhost',
        metavar='corenlp-server',
        help='Our assumption is that there is a CoreNLP server running; this argument captured the hostname on which '
             'it\'s running - but always on port 9000')


    args = arg_parser.parse_args()

    input_stream = open(args.input, encoding='utf-8') if args.input is not None else sys.stdin
    output_stream = open(args.output, 'w', encoding='utf-8', newline='') if args.output is not None else sys.stdout

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    ud_paths_from_tac(input_stream, output_stream, args.corenlp_server)
