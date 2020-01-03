import argparse
import json
import sys

import ijson
import requests
from stanfordcorenlp import StanfordCoreNLP

from path_to_re.internal.detokenizer import Detokenizer
from path_to_re.internal.link import Link
from path_to_re.internal.sync_tac_tags import SyncTacTags
from path_to_re.internal.ud_types import UdRepresentationPlaceholder
from path_to_re.internal.dep_graph import Step, DepGraph


class IndependentStanfordCoreNLP(StanfordCoreNLP):
    """
      IndependentStanfordCoreNLP wraps the 'StanfordCoreNLP' from the Lynten/stanford-corenlp package
      with the purpose of:
      1. providing a constructor that defaults to an external java Core NLP server
      2. providing an 'all_i_ever_wanted' method for extracting only the fields we're inerteres in.
      """

    def __init__(self, host, port, timeout):
        StanfordCoreNLP.__init__(self, path_or_host='http://{}'.format(host), port=port, timeout=timeout)

        # in case the server is still cold, let's warm it up
        self.all_i_ever_wanted("Let's get started here")

    def all_i_ever_wanted(self, sentences):
        sentences = sentences.encode('utf-8')

        properties = {
            'annotators': 'depparse',
            'ssplit.eolonly': 'true',
            'outputFormat': 'json'
        }

        params = {'properties': str(properties), 'pipelineLanguage': self.lang}

        r = requests.post(self.url, params=params, data=sentences)
        r_dict = json.loads(r.text)

        return r_dict


def collect_ud_paths_per_relation(input_stream, output_stream, corenlp_server):
    json_stream = ijson.items(input_stream, 'item')
    detokenizer = Detokenizer()
    core_nlp = IndependentStanfordCoreNLP(corenlp_server, 9000, 15000)

    for item in json_stream:

        relation = item['relation']
        if 'no_relation' == relation:
            continue

        tac_tokens = item['token']
        sentence = detokenizer.detokenize(tac_tokens)

        # we can access definitely access 'sentences' if 'all_i_ever_wanted' returned without error
        # and as we're only parsing one sentence at a time, we can access [0] for sure. I hope.
        parsed_sentence = core_nlp.all_i_ever_wanted(sentence)['sentences'][0]

        ud_parse = []
        for parse_dictionary in parsed_sentence['enhancedPlusPlusDependencies']:
            ud_parse.append((
                parse_dictionary['dependent'],
                parse_dictionary['dependentGloss'],
                parse_dictionary['dep'],
                parse_dictionary['governor'],
                parse_dictionary['governorGloss']))

        ud_tokens = [token['word'] for token in parsed_sentence['tokens']]

        tac_tokens_lookup = {
            'subj_start': item['subj_start'],
            'subj_end': item['subj_end'],
            'obj_start': item['obj_start'],
            'obj_end': item['obj_end']
        }
        ud_token_lookup = SyncTacTags.b_lookup_to_a_lookup(ud_tokens, tac_tokens, tac_tokens_lookup)

        if (len(ud_token_lookup) != len(tac_tokens_lookup)):
            print('were in trouble')

        ent1_start = ud_token_lookup['subj_start'] + 1
        ent1_end = ud_token_lookup['subj_end'] + 1

        ent2_start = ud_token_lookup['obj_start'] + 1
        ent2_end = ud_token_lookup['obj_end'] + 1

        links = UdRepresentationPlaceholder.get_links_from_ud_dep(ud_parse)
        ent1_head = Link.get_head(links, range(ent1_start, ent1_end + 1))
        ent2_head = Link.get_head(links, range(ent2_start, ent2_end + 1))

        graph = DepGraph(links)

        steps = graph.get_undirected_steps(ent1_head, ent2_head)
        steps_representation = Step.get_default_representation(steps)

        print('{relation}: {steps}'.format(relation=relation, steps=steps_representation))

        wait_here = True


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='collect_ud_paths_per_relation',
        description="receive a TACRED json file and produce a list of paths per relation")

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

    collect_ud_paths_per_relation(input_stream, output_stream, args.corenlp_server)
