import argparse
import csv
import sys
import time
import more_itertools


from path_to_re.internal.detokenizer import Detokenizer
from path_to_re.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe
from path_to_re.internal.core_nlp_client import CoreNlpClient
from path_to_re.internal.map_csv_column import CsvColumnMapper
from path_to_re.internal.sync_tags import SyncTags


def ner_from_csv(input_stream, output_stream, corenlp_server):

    csv_reader = csv.reader(input_stream)

    column_mapper = CsvColumnMapper(next(csv_reader), ['ner'],
                                    source_required=['id', 'docid', 'tokens', 'relation', 'path', 'type1', 'type2'])

    detokenizer = Detokenizer()

    core_nlp = CoreNlpClient(corenlp_server, 9000, 15000)

    csv_writer = csv.writer(output_stream)
    csv_writer.writerow(column_mapper.get_new_headers())


    #for count, entry in enumerate(csv_reader, start=0):
    count = 0
    for batch in more_itertools.chunked(csv_reader, 1):

        sentences = []
        for entry in batch:
            count += 1
            tokens = column_mapper.get_field_value_from_source(entry, 'tokens', True)
            sentence = detokenizer.detokenize(tokens)
            sentences.append(sentence)

        #tokens = column_mapper.get_field_value_from_source(entry, 'tokens', True)
        #sentence = detokenizer.detokenize(tokens)

        parsed_sentences = core_nlp.get_ner('\n'.join(sentences) )['sentences']

        for entry, sentence, parsed_sentence in zip(batch, sentences, parsed_sentences):

            tokens = column_mapper.get_field_value_from_source(entry, 'tokens', True)
            corenlp_tokens = [token['originalText'] for token in parsed_sentence['tokens']]
            ner_lookup_corenlp_tokenization = {}

            for entity_mention in parsed_sentence['entitymentions']:

                for index in range(entity_mention['tokenBegin'], entity_mention['tokenEnd']):
                    ner_lookup_corenlp_tokenization[index+1] = entity_mention['ner']


            ner_lookup = ner_lookup_corenlp_tokenization
            if tokens != corenlp_tokens and len(ner_lookup_corenlp_tokenization) > 0:
                ner_lookup = SyncTags.b_lookup_to_a_lookup(tokens, corenlp_tokens, ner_lookup_corenlp_tokenization)

            print('sentence: {}'.format(sentence))
            print('tokens: {}'.format([token['originalText'] for token in parsed_sentence['tokens']]))
            print('NER lookup: {}'.format(ner_lookup))



        #[token['word'] for token in look[0]['tokens']]



        #entity_mentions = look['sentences'][0]['entitymentions']

        wait_here = True

#        csv_writer.writerow([item['id'], item['docid'], relation, steps_representation, item['subj_type'], item['obj_type']])



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


    args = arg_parser.parse_args()

    input_stream = open(args.input, encoding='utf-8') if args.input is not None else sys.stdin
    output_stream = open(args.output, 'w', encoding='utf-8', newline='') if args.output is not None else sys.stdout

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    ner_from_csv(input_stream, output_stream, args.corenlp_server)
