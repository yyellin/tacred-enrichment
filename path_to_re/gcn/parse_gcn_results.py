"""Enhance TAC

Usage:
  parse_gcn_results.py [--input=<input-file>] [--output=<output-file>]
  parse_gcn_results.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
import sys
import csv
import re
from docopt import docopt

args = docopt(__doc__)

input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout

total_count = 0
csv_writer = None
in_result_block = False
pattern = r'(\S+)\s+P:\s+(\d+\.\d+)%\s+R:\s+(\d+.\d+)%\s+F1:\s+(\d+.\d+)%\s+#:\s+(\d+)'

for input_line in input_stream:
    if not in_result_block and 'Per-relation statistics:' in input_line:
        in_result_block = True
        csv_writer = csv.writer(output_stream)
        csv_writer.writerow(['relation', 'precision', 'recall', 'f1', 'count'])

    elif in_result_block:
        match = re.search(pattern, input_line)

        if match:
            relation = match.group(1)
            precision = round(float(match.group(2)) / 100, 4)
            recall = round(float(match.group(3)) / 100, 4)
            f1 = round(float(match.group(4)) / 100, 4)
            count = int(match.group(5))

            total_count += count

            csv_writer.writerow([relation, precision, recall, f1, count])
        else:
            in_result_block = False

    elif not in_result_block and 'Final Score:' in input_line:

        precision_line = next(input_stream)
        precision_match = re.search(r'Precision \(micro\):\s+(\d+.\d+)%', precision_line)
        if precision_match:
            precision = round(float(precision_match.group(1)) / 100, 4)
        else:
            exit(1)

        recall_line = next(input_stream)
        recall_match = re.search(r'Recall \(micro\):\s+(\d+.\d+)%', recall_line)
        if recall_match:
            recall = round(float(recall_match.group(1)) / 100, 4)
        else:
            exit(1)

        f1_line = next(input_stream)
        f1_match = re.search(r'F1 \(micro\):\s+(\d+.\d+)%', f1_line)
        if f1_match:
            f1 = round(float(f1_match.group(1)) / 100, 4)
        else:
            exit(1)

        csv_writer.writerow(['total', precision, recall, f1, total_count])
        exit(0)




