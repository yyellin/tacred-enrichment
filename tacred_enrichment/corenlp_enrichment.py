"""Enhance TAC with UD attributes based on CoreNLP parse

Usage:
  corenlp_enrichment.py <corenlp_server> <corenlp_port> [--lines] [--input=<input-file>] [--output=<output-file>]
  corenlp_enrichment.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
from docopt import docopt
import sys
import ijson
import jsonlines
from tacred_enrichment.internal.core_nlp_client import CoreNlpClient


def split_keep_delimiter(tokens, delimiter):

    fix_tokens = []

    for token in tokens:
        subtokens = token.split(delimiter)

        if len(subtokens) == 1:
            fix_tokens.append(token)

        else:
            fix_tokens.append(subtokens[0])

            for subtoken in subtokens[1:]:
                fix_tokens.append(delimiter)
                fix_tokens.append(subtoken)

    return fix_tokens



    #return [item for token in tokens for subtoken in token.split('.') for item in [subtoken, '.'] ]


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

        parse = core_nlp.get_all(retokenized, False)
        sentences = parse['sentences']

        item['corenlp_ner'] = []
        item['corenlp_pos'] = []
        item['corenlp_heads'] = []
        item['corenlp_coref'] = []

        for sentence in sentences:

            current_heads = [b for (a, b) in sorted([(dep_set['dependent'], dep_set['governor']) for dep_set in  sentence['basicDependencies']], key=lambda x: x[0])]
            current_heads = [head + len(item['corenlp_heads']) if head > 0 else head for head in current_heads]

            current_pos = [token['pos'] for token in sentence['tokens']]
            current_ner = [token['ner'] for token in sentence['tokens']]

            item['corenlp_heads'] += current_heads
            item['corenlp_pos'] += current_pos
            item['corenlp_ner'] += current_ner


        sentence_adj = [0]
        for sentence in sentences[:-1]:
            sentence_adj.append( len(sentence['tokens']) )

        corefs = parse['corefs'].values()

        for coref in corefs:
            anchor = next(x for x in coref if x['isRepresentativeMention'])
            refs = [x for x in coref if not x['isRepresentativeMention']]

            anchor_coords = [anchor['startIndex']+sentence_adj[anchor['sentNum']-1], \
                            anchor['endIndex']+sentence_adj[anchor['sentNum']-1]]

            refs_coords = [[ref['startIndex']+sentence_adj[ref['sentNum']-1], \
                            ref['endIndex']+sentence_adj[ref['sentNum']-1]] for ref in refs]

            item['corenlp_coref'].append([anchor_coords, refs_coords])

        json_write.write(item)



