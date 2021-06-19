import argparse
import csv
import sys

import ijson

from tacred_enrichment.internal.dep_graph import Step, DepGraph
from tacred_enrichment.internal.detokenizer import Detokenizer
from tacred_enrichment.internal.link import Link
from tacred_enrichment.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe
from tacred_enrichment.internal.map_tokenization import MapTokenization
from tacred_enrichment.internal.ud_types import UdRepresentationPlaceholder
from tacred_enrichment.internal.core_nlp_client import CoreNlpClient





def ud_paths_from_tac(input_stream, output_stream, corenlp_server):
    json_stream = ijson.items(input_stream, 'item')
    detokenizer = Detokenizer()
    core_nlp = CoreNlpClient(corenlp_server, 9000, 15000)
    csv_writer = csv.writer(output_stream)
    csv_writer.writerow(['id', 'docid', 'tokens', 'relation', 'path', 'lemmas_on_path', 'type1', 'type2', 'ent1_head', 'ent2_head'])


    for item in json_stream:

        relation = item['relation']

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

        ud_tokens = [token['originalText'] for token in parsed_sentence['tokens']]
        ud_lemmas = [token['lemma'] for token in parsed_sentence['tokens']]


        token_map = MapTokenization.map_a_to_b(tac_tokens, ud_tokens)

        if  item['subj_start'] not in token_map \
            or item['subj_end'] not in token_map \
            or item['obj_start'] not in token_map \
            or item['obj_end'] not in token_map:
            print('failed to map "tac tokenization" to "ud tokenization"')
            continue


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

        lemmas_on_path = [ud_lemmas[step.me-1] for step in steps[1:]]

        csv_writer.writerow(
            [item['id'],
             item['docid'],
             ud_tokens,
             relation,
             steps_representation,
             lemmas_on_path,
             item['subj_type'],
             item['obj_type'],
             ent1_head,
             ent2_head])

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
