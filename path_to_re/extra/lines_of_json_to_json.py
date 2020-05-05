"""Lines of json to json

Usage:
  lines_of_json_to_json.py [--skip=<fields-to-skip>] [--input=<input-file>] [--output=<output-file>]

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
    fields_to_skip = [field for field in args['--skip'].split(',')] if args['--skip'] is not None else []

    entries = []
    with jsonlines.Reader(input_stream) as json_reader:
        for entry in json_reader:
            for field_to_skip in fields_to_skip:
                del entry[field_to_skip]

            entries.append(entry)

    with output_stream:
        json.dump(entries, output_stream)
