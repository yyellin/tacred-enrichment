import argparse
import csv
import json
import sys

from tacred_enrichment.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe


def convert_tac_to_csv(input, output, relation):
    """

     Parameters
     ----------

     Returns
     -------

    """

    json_input = json.load(input)
    csv_out = csv.writer(output, lineterminator='\n')

    fieldnames = ['tac_doc_id', 'tac_sentence_id', 'tac_tokens', 'subj_start', 'subj_end', 'obj_start', 'obj_end']
    csv_out.writerow(fieldnames)

    for entry in json_input:
        if not relation is None and entry['relation'] != relation:
            continue

        tokens = entry['token']
        subj_start = entry['subj_start']
        subj_end = entry['subj_end']
        obj_start = entry['obj_start']
        obj_end = entry['obj_end']
        tac_doc_id =  entry['docid']
        tac_sentence_id = entry['id']


        csv_out.writerow([tac_doc_id, tac_sentence_id, tokens, subj_start, subj_end, obj_start, obj_end])


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='tac_to_csv',
        description='convert json TAC file to a comma-separated value '
                    'file with the following columns: '
                    'tac_tokens, ent1_start, ent1_end, ent2_start, ent2_end')

    arg_parser.add_argument(
        '--relation',
        action='store',
        metavar='relation-string',
        help='only convert relations of this type, ignore all others')

    arg_parser.add_argument(
        '--input',
        action='store',
        metavar='input-file',
        help='when provided input will be read from this file rather than from standard input')

    arg_parser.add_argument(
        '--output',
        action='store',
        metavar='output-file',
        help='when provided output will be written to this file rather than to standard output')

    args = arg_parser.parse_args()

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    input = open(args.input, encoding='utf-8') if args.input is not None else sys.stdin
    output = open(args.output, 'w', encoding='utf-8', newline='') if args.output is not None else sys.stdout

    convert_tac_to_csv(input, output, args.relation)
