"""json to lines of json

Usage:
  json_to_lines_of_json.py [--input=<input-file>] [--output=<output-file>]

Options:
  -h --help     Show this screen.
"""
import sys
import json
import ijson
from docopt import docopt



if __name__ == "__main__":
    args = docopt(__doc__)

    input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
    output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout

    json_stream = ijson.items(input_stream, 'item')

    for entry in json_stream:
        json.dump(entry, output_stream)
        output_stream.write('\n')
