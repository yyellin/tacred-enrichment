"""corenlp_attributes

Usage:
  corenlp_attributes.py <corenlp_server> <corenlp_port> [--lines] [--input=<input-file>] [--output=<output-file>]
  corenlp_attributes.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
from docopt import docopt
import sys
import ijson
import jsonlines
from path_to_re.internal.core_nlp_client import CoreNlpClient


args = docopt(__doc__)

corenlp_server = args['<corenlp_server>']
corenlp_port = int(args['<corenlp_port>'])

input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout
lines = True if args['--lines'] else False

reader = jsonlines.Reader(input_stream) if lines else ijson.items(input_stream, 'item')

with jsonlines.Writer(output_stream) as json_write:
    core_nlp = CoreNlpClient(corenlp_server, corenlp_port, 15000)

    for item in reader:

        retokenized = item['ucca_tokens']

        parsed_sentence = core_nlp.get_all(retokenized, False)['sentences'][0]

        item['corenlp_ner'] = [token['ner'] for token in parsed_sentence['tokens']]
        item['corenlp_pos'] = [token['pos'] for token in parsed_sentence['tokens']]
        item['corenlp_heads'] = [b for (a, b) in sorted(
            [(dep_set['dependent'], dep_set['governor']) for dep_set in  parsed_sentence['basicDependencies']],
            key=lambda x: x[0])]

        json_write.write(item)



