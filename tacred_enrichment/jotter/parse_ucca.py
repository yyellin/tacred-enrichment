import argparse
import csv
import sys

from tacred_enrichment.internal.detokenizer import Detokenizer
from tacred_enrichment.internal.map_csv_column import CsvColumnMapper
from tacred_enrichment.internal.mnofc import ManageNewOutputFileCreation
from tacred_enrichment.internal.sync_tac_tags import SyncTacTags
from tacred_enrichment.internal.tupa_parser import TupaParser
from tacred_enrichment.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe

def parse_ucca(model_prefix, input_file=None, output_file=None, batch_size=None):
    """

     Parameters
     ----------

     Returns
     -------

    """
    input = open(input_file, encoding='utf-8') if input_file is not None else sys.stdin
    csv_reader = csv.reader(input)

    column_mapper = CsvColumnMapper(
        source_first_row=next(csv_reader),
        new_columns=
        ['sentence',
         'ent1',
         'ent2',
         'ent1_start',
         'ent1_end',
         'ent2_start',
         'ent2_end',
         'ucca_parse',
         'words',
         'lemmas',
         'parse_ucca_comment'],
        source_required=
        ['tac_tokens',
         'subj_start',
         'subj_end',
         'obj_start',
         'obj_end'],
        filter_source_from_result=
        ['tac_tokens',
         'subj_start',
         'subj_end',
         'obj_start',
         'obj_end']
    )

    detokenizer = Detokenizer()
    mnofc = ManageNewOutputFileCreation(output_file, batch_size)

    print('BEGIN-INIT-TUPA')
    parser = TupaParser(model_prefix)
    print('END-INIT-TUPA')

    for count, entry in enumerate(csv_reader, start=0):

        new_file = mnofc.get_new_file_if_necessary()
        if new_file:
            csv_writer = csv.writer(new_file)
            csv_writer.writerow(column_mapper.get_new_headers())

        tac_tokens = eval(column_mapper.get_field_value_from_source(entry, 'tac_tokens'))
        sentence = detokenizer.detokenize(tac_tokens)

        print('BEGIN-PROCESS-TUPA')
        parsed_sentence = parser.parse_sentence(sentence)
        print('END-PROCESS-TUPA')

        tokens = []
        tokens_with_indices = []
        lemmas_with_indices = []

        for ucca_terminal in parsed_sentence.terminals:
            tokens.append(ucca_terminal.text)
            tokens_with_indices.append((ucca_terminal.token_id, ucca_terminal.text))
            lemmas_with_indices.append((ucca_terminal.token_id, ucca_terminal.lemma))

        tac_tokens_lookup = {}
        tac_tokens_lookup['subj_start'] = int(column_mapper.get_field_value_from_source(entry, 'subj_start'))
        tac_tokens_lookup['subj_end'] = int(column_mapper.get_field_value_from_source(entry, 'subj_end'))
        tac_tokens_lookup['obj_start'] = int(column_mapper.get_field_value_from_source(entry, 'obj_start'))
        tac_tokens_lookup['obj_end'] = int(column_mapper.get_field_value_from_source(entry, 'obj_end'))

        token_lookup = SyncTacTags.b_lookup_to_a_lookup(tokens, tac_tokens, tac_tokens_lookup)

        if len(token_lookup) != len(tac_tokens_lookup):
            csv_writer.writerow(column_mapper.get_new_row_values(entry,
                                                                 [sentence,
                                                                  None,
                                                                  None,
                                                                  None,
                                                                  None,
                                                                  None,
                                                                  None,
                                                                  None,
                                                                  None,
                                                                  None,
                                                                  'was not able to reconcile TAC and Tupa\'s Spacy based indexing']))
            continue

        ent1_start = token_lookup['subj_start']
        ent1_end = token_lookup['subj_end']
        ent1 = ' '.join(tokens[ent1_start:ent1_end + 1])

        ent2_start = token_lookup['obj_start']
        ent2_end = token_lookup['obj_end']
        ent2 = ' '.join(tokens[ent2_start:ent2_end + 1])

        csv_writer.writerow(column_mapper.get_new_row_values(entry,
                                                             [sentence,
                                                              ent1,
                                                              ent2,
                                                              ent1_start + 1,
                                                              ent1_end + 1,
                                                              ent2_start + 1,
                                                              ent2_end + 1,
                                                              parsed_sentence.serialize(),
                                                              tokens_with_indices,
                                                              lemmas_with_indices,
                                                              None]))




if __name__ == "__main__":

    # following is the proper args string
    # ../../tupa/models/bert_multilingual_layers_4_layers_pooling_weighted_align_sum
    # --input ../../tacred/results/org-founded_by/train/tac.csv
    # --output ../../tacred/results/org-founded_by/train/ucca-work-on-serialization.csv
    arg_parser = argparse.ArgumentParser(
        prog='parse_ucca',
        description='prepare each sentence represented by an entry in the comma-separated value input '
                    'for ucca based path analysis. '
                    'Each entry will be supplemented with additional columns '
                    'ent1, ent2, ucca_parse, tokens, lemmas. '
                    '(Tokenization is according to ucca and not the input tokens)')

    arg_parser.add_argument(
        'model',
        action='store',
        metavar='model-path-prefix',
        help='path and then the prefix of the model as a single string (for example:'
             '../../tupa/models/bert_multilingual_layers_4_layers_pooling_weighted_align_sum')


    arg_parser.add_argument(
        '--input',
        action='store',
        metavar='input-file',
        help='when provided input will be read from this file rather than from standard input')

    arg_parser.add_argument(
        '--output',
        action='store',
        metavar='output-file',
        help='when provided output will be written to this file rather than standard output')

    arg_parser.add_argument(
        '--batch-size',
        metavar='batch size',
        nargs='?',
        default=None,
        type=int,
        help="it's possible to generate the output file in batches (will be ignored if input is being written to standard output)")

    args = arg_parser.parse_args()

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    parse_ucca( args.model, input_file=args.input, output_file=args.output, batch_size=args.batch_size)
