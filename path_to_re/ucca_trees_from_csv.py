import argparse
import csv
import sys
import numpy


from path_to_re.internal.dep_graph import DepGraph
from path_to_re.internal.link import Link
from path_to_re.internal.map_csv_column import CsvColumnMapper
from path_to_re.internal.ucca_types import UccaParsedPassage
from path_to_re.internal.tree_as_string import draw_tree, node_constructor


def assign_ucca_tree(input, output):
    csv_reader = csv.reader(input)
    csv_writer = csv.writer(output)

    column_mapper = CsvColumnMapper(
        next(csv_reader),
        new_columns=['ucca_tree', 'ucca_tree_comment'],
        source_required=['tac_doc_id',
                         'tac_sentence_id',
                         'sentence',
                         'ent1_start',
                         'ent1_end',
                         'ent2_start',
                         'ent2_end',
                         'words',
                         'ner',
                         'ucca_parse'
                         ])

    csv_writer.writerow(column_mapper.get_new_headers())

    for counter, entry in enumerate(csv_reader, start=1):

        print('Processing sentence #{}'.format(column_mapper.get_field_value_from_source(entry, 'tac_sentence_id')))
        sentence = column_mapper.get_field_value_from_source(entry, 'sentence')

        if 'STEVEN B DEROUNIAN' in sentence:
            break_here = True

    #     ┌─── STEVEN
    #     │
    #     ├──────── B
    # ┌ A - ent1 ┤
    # │        ├ DEROUNIAN
    # │        │
    # * ┤        └──── JUDGE
    # │
    # ├───── P ──── moving
    # │
    # │        ┌──────── R ───── to
    # └───── A ┤
    # └─── C - ent2 ─ Austin

        ucca_parse_serialization = column_mapper.get_field_value_from_source(entry, 'ucca_parse')
        if ucca_parse_serialization is None:
            csv_writer.writerow(column_mapper.get_new_row_values(entry, [None, None, 'ucca_parse missing']))
            continue

        ner = column_mapper.get_field_value_from_source(entry, 'ner', evaluate=True)
        if ner is None:
            csv_writer.writerow(column_mapper.get_new_row_values(entry, [None, None, 'ner missing']))
            continue

        ent1_start_token_id = column_mapper.get_field_value_from_source(entry, 'ent1_start', as_int=True)
        ent1_end_token_id = column_mapper.get_field_value_from_source(entry, 'ent1_end', as_int=True)

        ent1_indicative_token = 0
        for ent1_token_id in range(ent1_start_token_id, ent1_end_token_id+1):
            if ent1_token_id in ner and 'PERSON' in ner[ent1_token_id]:
                ent1_indicative_token = ent1_token_id
                break

        if ent1_indicative_token == 0:
            csv_writer.writerow(column_mapper.get_new_row_values(entry, [None, None, 'ent1 does not match \'PERSON\'']))
            continue


        ent2_start_token_id = column_mapper.get_field_value_from_source(entry, 'ent2_start', as_int=True)
        ent2_end_token_id = column_mapper.get_field_value_from_source(entry, 'ent2_end', as_int=True)

        ent2_indicative_token = 0
        for ent2_token_id in range(ent2_start_token_id, ent2_end_token_id+1):
            if ent2_token_id in ner and 'GPE' in ner[ent2_token_id]:
                ent2_indicative_token = ent2_token_id
                break

        if ent2_indicative_token == 0:
            csv_writer.writerow(column_mapper.get_new_row_values(entry, [None, None, 'ent2 does not match \'PERSON\'']))
            continue



        ucca_parse = UccaParsedPassage.from_serialization(ucca_parse_serialization)
        ucca_dag_links = ucca_parse.get_links()


        ent1_indicative_token_node_id = ucca_parse.get_node_id_by_token_id(ent1_indicative_token)
        ent1_indicative_token_parent_node_ids = Link.get_parents(ucca_dag_links, ent1_indicative_token_node_id)
        if len(ent1_indicative_token_parent_node_ids) == 0:
            csv_writer.writerow(column_mapper.get_new_row_values(entry, [None, None, 'Could not find parent of indicative token for ent1']))
            continue
        # we don't expect terminals to have more than one parent
        ent1_indicative_token_parent_node_id = ent1_indicative_token_parent_node_ids[0]


        ent2_indicative_token_node_id = ucca_parse.get_node_id_by_token_id(ent2_indicative_token)
        ent2_indicative_token_parent_node_ids = Link.get_parents(ucca_dag_links, ent2_indicative_token_node_id)
        if len(ent2_indicative_token_parent_node_ids) == 0:
            csv_writer.writerow(column_mapper.get_new_row_values(entry, [None, None, 'Could not find parent of indicative token for ent2']))
            continue
        # we don't expect terminals to have more than one parent
        ent2_indicative_token_parent_node_id = ent2_indicative_token_parent_node_ids[0]



        dag = DepGraph(ucca_dag_links, is_terminal)
        ucca_subdag_links = dag.get_links_of_lca_subgraph(ent1_indicative_token_parent_node_id, ent2_indicative_token_parent_node_id)


        subdag = DepGraph(ucca_subdag_links, is_terminal)
        link_lookup = { (link.parent_index, link.word_index) : link for link in ucca_subdag_links}

        root = subdag.root()

        # to understand what this code is doing first take a look
        # at the example in the 'tree_as_string' module - here too
        # we're basically doing a depth first traversal of the tree
        # creating a tree of 'node_constructor' objects, and then calling
        # 'draw_tree' to produce text


        def extract_tree_node_recursively (parent, current):

            full_node_text = '*'

            if not parent is None:
                link = link_lookup[(parent, current)]

                # the logic here is that if we're a terminal we output the actual word rather
                # than the dependency type (which will be 'Terminal' ..)
                # and then we prepend the term 'ent1' or 'ent2' if indeed that's the case

                core_node_text = link.word if link.dep_type == 'Terminal' else link.dep_type
                full_node_text = core_node_text

                if current == ent1_indicative_token_parent_node_id:
                    full_node_text = '{0}-ent1'.format(core_node_text)
                elif current == ent2_indicative_token_parent_node_id:
                    full_node_text = '{0}-ent2'.format(core_node_text)

            next_gen_nodes = []
            for nextgen in subdag.successors(current):
                next_gen_nodes.append(extract_tree_node_recursively(current, nextgen))

            return node_constructor(full_node_text)(next_gen_nodes)



        extract_tree_output = extract_tree_node_recursively(None, root)

        ucca_subtree_as_text = draw_tree(False)(False)(extract_tree_output)

        # # let's fucking flip it.
        # lines = ucca_subtree_as_text.split(sep='\n')
        # longest_line_len = len(max(lines, key=len))
        #
        # padded_lines = [line.ljust(longest_line_len, ' ') for line in lines]
        #
        # n_array =  numpy.array([list(padded_line) for padded_line in padded_lines])
        # n_array = numpy.rot90(n_array, 3)
        #
        # flipped_lines = []
        #
        # for flipped_line_as_array in n_array.tolist():
        #     flipped_line = ''.join(flipped_line_as_array)
        #     flipped_lines.append(flipped_line)
        #
        # flipped_text = '\n'.join(flipped_lines)
        #



        no_comment = None

        csv_writer.writerow(column_mapper.get_new_row_values(entry, [ucca_subtree_as_text, no_comment]))

        wait_here = True

        # for count, (segment1, segment2) in enumerate(product(ent1_to_trigger_strings, trigger_to_ent2_strings),
        #                                              start=1):
        #     path_id = '{0}_{1}'.format(sentence_id, count)
        #     path = '{0} >< {1}'.format(segment1, segment2)
        #
        #     #pattern = '^.*\^A \!P >< \^P \!A.*$'
        #     #if re.search(pattern, path):
        #     #    path = '^A !P >< ^P !A'
        #
        #     comment = None
        #
        #     csv_writer.writerow(column_mapper.get_new_row_values(entry, [path_id, path, comment]))



if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='assign_ucca_tree',
        description='for each row in input add ucca tree')

    arg_parser.add_argument(
        '--input',
        action='store',
        metavar='input-file',
        help='When provided input will be read from this file rather than from standard input')

    arg_parser.add_argument(
        '--output',
        action='store',
        metavar='output-file',
        help='The comma-separated field output file')

    args = arg_parser.parse_args()

    input = open(args.input, encoding='utf-8') if args.input is not None else sys.stdin
    output = open(args.output, 'w', encoding='utf-8', newline='') if args.output is not None else sys.stdout

    assign_ucca_tree(input, output)

