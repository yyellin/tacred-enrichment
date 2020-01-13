import argparse
import csv
import sys
import time

import ijson
import more_itertools

from path_to_re.internal.dep_graph import Step, DepGraph
from path_to_re.internal.detokenizer import Detokenizer
from path_to_re.internal.link import Link
from path_to_re.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe
from path_to_re.internal.sync_tac_tags import SyncTacTags
from path_to_re.internal.tupa_parser import TupaParser



def collect_ucca_paths_per_relation(input_stream, output_stream, model_prefix, sentence_batch_size):

    parser = TupaParser(model_prefix)
    json_stream = ijson.items(input_stream, 'item')
    detokenizer = Detokenizer()
    csv_writer = csv.writer(output_stream)
    csv_writer.writerow(['id', 'docid', 'relation', 'path', 'type1', 'type2'])

    #for batch in more_itertools.chunked(filter(lambda item: item['relation'] != 'no_relation', json_stream), sentence_batch_size):
    for batch in more_itertools.chunked(json_stream, sentence_batch_size):
        sentences = []
        for item in batch:
            tac_tokens = item['token']
            sentence = detokenizer.detokenize(tac_tokens)
            sentences.append(sentence)

        t0 = time.time()
        parsed_sentences = parser.parse_sentences(sentences)
        t1 = time.time()
        print('Parsed {batch} sentences in {duration}'.format(batch=len(batch), duration=t1-t0))

        for item, sentence, parsed_sentence in zip(batch, sentences, parsed_sentences):

            tac_tokens = item['token']
            ucca_tokens = [ucca_terminal.text for ucca_terminal in parsed_sentence.terminals]

            tac_tokens_lookup = {
                'subj_start': item['subj_start'],
                'subj_end': item['subj_end'],
                'obj_start': item['obj_start'],
                'obj_end': item['obj_end']
            }
            ucca_token_lookup = SyncTacTags.b_lookup_to_a_lookup(ucca_tokens, tac_tokens, tac_tokens_lookup)

            if (len(ucca_token_lookup) != len(tac_tokens_lookup)):
                print('unable to reconcile UCCA tokens with TAC tokens')
                continue

            ent1_start = ucca_token_lookup['subj_start'] + 1
            ent1_end = ucca_token_lookup['subj_end'] + 1

            ent2_start = ucca_token_lookup['obj_start'] + 1
            ent2_end = ucca_token_lookup['obj_end'] + 1

            links = parsed_sentence.get_links()

            ent1_start_node_id = parsed_sentence.get_node_id_by_token_id(ent1_start)
            ent1_parent_node_ids = Link.get_parents(links, ent1_start_node_id)
            if len(ent1_parent_node_ids) == 0:
                print('trouble identifying start node for ent1')
                continue
            ent1_parent_node_id = ent1_parent_node_ids[0]

            ent2_start_node_id = parsed_sentence.get_node_id_by_token_id(ent2_start)
            ent2_parent_node_ids = Link.get_parents(links, ent2_start_node_id)
            if len(ent2_parent_node_ids) == 0:
                print('trouble identifying start node for ent2')
                continue
            ent2_parent_node_id = ent2_parent_node_ids[0]

            graph = DepGraph(links)

            steps = graph.get_undirected_steps(ent1_parent_node_id, ent2_parent_node_id)
            steps_representation = Step.get_default_representation(steps)

            csv_writer.writerow([item['id'], item['docid'], item['relation'] , steps_representation, item['subj_type'], item['obj_type']])

            wait_here = True



if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='collect_ucca_paths_per_relation',
        description="receive a TACRED json file and produce a list of UCCA paths per relation")

    arg_parser.add_argument(
        '--model-prefix',
        action='store',
        metavar='model-path-prefix',
        default=r'..\..\tupa\models\bert_multilingual_layers_4_layers_pooling_weighted_align_sum',
        help='path and then the prefix of the model as a single string (for example:'
             '../../tupa/models/bert_multilingual_layers_4_layers_pooling_weighted_align_sum')

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
        '--batch-size',
        metavar='sentence-batch-size',
        nargs='?',
        default=10,
        type=int,
        help="how many sentences to batch together for the actual TUPA parse machine")



    args = arg_parser.parse_args()

    input_stream = open(args.input, encoding='utf-8') if args.input is not None else sys.stdin
    output_stream = open(args.output, 'w', encoding='utf-8', newline='', buffering=1) if args.output is not None else sys.stdout

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    collect_ucca_paths_per_relation(input_stream, output_stream, args.model_prefix, args.batch_size)
