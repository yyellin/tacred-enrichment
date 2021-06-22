"""sentences_per_entry

Usage:
  sentences_per_entry.py <corenlp_server> <corenlp_port> [--input=<input-file>] [--output=<output-file>]
  sentences_per_entry.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
import sys
import ijson
import jsonlines

from docopt import docopt

from tacred_enrichment.internal.core_nlp_client import CoreNlpClient
from tacred_enrichment.internal.sanitize_tacred import SanitizeTacred
from tacred_enrichment.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe


def get_number_of_sentences(sentence, core_nlp):
    parse = core_nlp.get_as_little_as_possible(sentence)

    sentences = parse['sentences']

    return len(sentences)


def sentences_per_entry(input_stream, output_stream, corenlp_server, corenlp_port):

    json_read = ijson.items(input_stream, 'item')

    with jsonlines.Writer(output_stream) as json_write:

        core_nlp = CoreNlpClient(corenlp_server, corenlp_port, 15000)

        for item in json_read:
            sentence = ' '.join(SanitizeTacred.sanitize_tokens(item['token']))

            sentence_count = get_number_of_sentences(sentence, core_nlp)

            item['sentence_count'] = sentence_count

            json_write.write(item)


if __name__ == "__main__":
    args = docopt(__doc__)

    input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
    output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout
    corenlp_server = args.get('<corenlp_server>', None)
    corenlp_port = args.get('<corenlp_port>', '-1')
    corenlp_port = int(corenlp_port) if corenlp_port is not None else -1

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    sentences_per_entry(input_stream, output_stream, corenlp_server, corenlp_port)

