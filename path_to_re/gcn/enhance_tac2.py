"""UCCA For TAC

Usage:
  enhance_tac2.py <tupa_module_path>  [--input=<input-file>] [--output=<output-file>]
  enhance_tac2.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
import sys
import ijson
import jsonlines
from semstr.convert import to_conllu
from conllu import parse as conllu_parse

from docopt import docopt

from path_to_re.internal.sanitize_tacred import SanitizeTacred
from path_to_re.internal.map_tokenization import MapTokenization
from path_to_re.internal.pipe_error_work_around import revert_to_default_behaviour_on_sigpipe
from path_to_re.internal.tupa_parser import TupaParser



def enhance_tac2(input_stream, output_stream, model_prefix):

    json_read = ijson.items(input_stream, 'item')

    with jsonlines.Writer(output_stream) as json_write:

        parser = TupaParser(model_prefix)


        for item in json_read:
            sentence = ' '.join(SanitizeTacred.sanitize_tokens(item['token']))
            parsed_sentence = parser.parse_sentence(sentence)
            if parsed_sentence is None:
                print('failed to perform UCCA parse')
                continue

            sanitized_tac_tokens = SanitizeTacred.sanitize_tokens(item['token'])
            ucca_tokens = [ucca_terminal.text for ucca_terminal in parsed_sentence.terminals]
            tac_to_ucca = MapTokenization.map_a_to_b(sanitized_tac_tokens, ucca_tokens)

            #ensure tac_to_ucca is 'surjective' over 'ucca_tokens':
            tac_to_ucca_coverage = {ucca_token: True for ucca_tokens in tac_to_ucca.values() for ucca_token in ucca_tokens}
            if (len(tac_to_ucca_coverage) != len(ucca_tokens)) \
                    or (0 not in tac_to_ucca_coverage) \
                    or ((len(tac_to_ucca_coverage)-1) not in tac_to_ucca_coverage):
                print('failed to align all UCCA and TACRED tokens for UCCA head/dep extraction')
                continue

            #ensure tac_to_ucca range is defined over 'sanitized_tac_tokens'
            tac_to_ucca_defined = {tac_token: True for tac_token in tac_to_ucca.keys()}
            if (len(tac_to_ucca_defined) != len(sanitized_tac_tokens)) \
                    or (0 not in tac_to_ucca_defined) \
                    or ((len(tac_to_ucca_defined)-1) not in tac_to_ucca_defined):
                print('failed to align all UCCA and TACRED tokens for UCCA head/dep extraction')
                continue

            item['tac_to_ucca'] = tac_to_ucca
            item['ucca_tokens'] = ucca_tokens

            # # handle subject + object
            # item['subj_start_ucca'] = tac_to_ucca[item['subj_start']][0]
            # item['subj_end_ucca'] = tac_to_ucca[item['subj_end']][-1]
            # item['obj_start_ucca'] = tac_to_ucca[item['obj_start']][0]
            # item['obj_end_ucca'] = tac_to_ucca[item['obj_end']][-1]
            #
            # # handle 'stanford pos'
            # stanford_pos = item['stanford_pos']
            # ucca_standford_pos_dict = { ucca_token:pos for tac_token, pos in enumerate(stanford_pos) for ucca_token in tac_to_ucca[tac_token]}
            # item['standford_pos_ucca'] = [pos for key, pos in sorted(ucca_standford_pos_dict.items())]
            #
            # # handle 'stanford ner'
            # stanford_ner = item['stanford_ner']
            # ucca_standford_ner_dict = { ucca_token:ner for tac_token, ner in enumerate(stanford_ner) for ucca_token in tac_to_ucca[tac_token]}
            # item['standford_ner_ucca'] = [ner for key, ner in sorted(ucca_standford_ner_dict.items())]

            lines_representation = to_conllu(parsed_sentence.native)
            conllu = conllu_parse('\n'.join(lines_representation))
            item['ucca_heads'] = [token_info['head'] for i, token_info in enumerate(conllu[0])]
            item['ucca_deps'] = [token_info['deps'] for i, token_info in enumerate(conllu[0])]

            item['ucca_tags'] = [ucca_terminal.tag for ucca_terminal in parsed_sentence.terminals]
            item['ucca_poss'] = [ucca_terminal.pos for ucca_terminal in parsed_sentence.terminals]
            item['ucca_ents'] = [ucca_terminal.ent for ucca_terminal in parsed_sentence.terminals]
            item['ucca_parse'] = parsed_sentence.serialize()

            json_write.write(item)


if __name__ == "__main__":
    args = docopt(__doc__)

    input_stream = open(args['--input'], encoding='utf-8') if args['--input'] is not None else sys.stdin
    output_stream = open(args['--output'], 'w', encoding='utf-8', newline='', buffering=1) if args['--output'] is not None else sys.stdout
    tupa_module_path = args.get('<tupa_module_path>', None)

    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    revert_to_default_behaviour_on_sigpipe()

    enhance_tac2(input_stream, output_stream, tupa_module_path)

