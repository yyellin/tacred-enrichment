import argparse
import csv
import sys
import more_itertools

from tacred_enrichment.internal.map_tokenization import MapTokenization
from tacred_enrichment.internal.detokenizer import Detokenizer
from tacred_enrichment.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe
from tacred_enrichment.internal.core_nlp_client import CoreNlpClient
from tacred_enrichment.internal.map_csv_column import CsvColumnMapper


def ner_from_csv(input_stream, output_stream, corenlp_server, sentence_batch_size):

    csv_reader = csv.reader(input_stream)

    column_mapper = CsvColumnMapper(next(csv_reader), ['type1_corenlp', 'type2_corenlp'],
                                    source_required=['id', 'docid', 'tokens', 'relation', 'path', 'type1', 'type2', 'ent1_head', 'ent2_head'])

    detokenizer = Detokenizer()

    core_nlp = CoreNlpClient(corenlp_server, 9000, 45000)

    csv_writer = csv.writer(output_stream)
    csv_writer.writerow(column_mapper.get_new_headers())

    count = 0
    for batch in more_itertools.chunked(csv_reader, sentence_batch_size):

        sentences = []
        for entry in batch:
            count += 1
            tokens = column_mapper.get_field_value_from_source(entry, 'tokens', True)
            sentence = detokenizer.detokenize(tokens)
            sentences.append(sentence)

        parsed_sentences = core_nlp.get_ner('\n'.join(sentences) )['sentences']

        for entry, sentence, parsed_sentence in zip(batch, sentences, parsed_sentences):

            tokens = column_mapper.get_field_value_from_source(entry, 'tokens', True)
            corenlp_tokens = [token['originalText'] for token in parsed_sentence['tokens']]

            token_map = MapTokenization.map_a_to_b(corenlp_tokens, tokens)

            ner_lookup = {}

            for entity_mention in parsed_sentence['entitymentions']:
                for index in range(entity_mention['tokenBegin'], entity_mention['tokenEnd']):
                    if index in token_map:
                        fixed_index = token_map[index][0]
                        ner_lookup[fixed_index] = entity_mention['ner']

            ent1_head = column_mapper.get_field_value_from_source(entry, 'ent1_head', as_int=True)
            ent2_head = column_mapper.get_field_value_from_source(entry, 'ent2_head', as_int=True)

            type1_corenlp = ner_lookup.get(ent1_head, '')
            type2_corenlp = ner_lookup.get(ent2_head, '')

            csv_writer.writerow(column_mapper.get_new_row_values(entry, [type1_corenlp, type2_corenlp]))




if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='ner_from_csv',
        description="for each row in input add NER output from Standford Core NLP")

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


    arg_parser.add_argument(
        '--batch-size',
        metavar='sentence-batch-size',
        default=1,
        type=int,
        help="how many sentences to batch together for the CoreNLP parse call")


    args = arg_parser.parse_args()

    input_stream = open(args.input, encoding='utf-8') if args.input is not None else sys.stdin
    output_stream = open(args.output, 'w', encoding='utf-8', newline='') if args.output is not None else sys.stdout

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    ner_from_csv(input_stream, output_stream, args.corenlp_server, args.batch_size)
