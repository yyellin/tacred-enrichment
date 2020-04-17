"""Lines of json to json

Usage:
  lines_of_json_to_json.py [--input=<input-file>] [--output=<output-file>]

Options:
  -h --help     Show this screen.
"""
import sys
import json
import jsonlines
from docopt import docopt



if __name__ == "__main__":
    args = docopt(__doc__)

    input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
    output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout

    entries = []
    with jsonlines.Reader(input_stream) as json_reader:
        for entry in json_reader:
            entries.append(entry)

    with output_stream:
        json.dump(entries, output_stream)
