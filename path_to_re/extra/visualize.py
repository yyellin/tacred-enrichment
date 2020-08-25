"""Visualize

Usage:
  visualize.py raw <tupa_module_path> <input-file> <output-dir>
  visualize.py xml_serializion <input-file> <output-dir>
  visualize.py my_serialization <input-file> <output-dir>
  visualize.py (-h | --help)

Options:
  -h --help     Show this screen.
"""


import os
import warnings
from docopt import docopt
from collections import defaultdict
from operator import attrgetter

import matplotlib
import matplotlib.pyplot as plt

from ucca import layer0, layer1
from ucca.ioutil import get_passages_with_progress_bar

from path_to_re.internal.ucca_types import UccaParsedPassage, UccaTerminalNode



def from_xml(xml_files, output_dir):

    passages = get_passages_with_progress_bar(xml_files, desc="Visualizing")

    for passage in passages:

        width = len(passage.layer(layer0.LAYER_ID).all) * 19 / 27
        plt.figure(figsize=(width, width * 10 / 19))
        draw_from_native(passage)

        plt.savefig(os.path.join(output_dir, passage.ID + ".png"))
        plt.close()

def draw_from_native(passage):
    import matplotlib.cbook
    import networkx as nx
    warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
    warnings.filterwarnings("ignore", category=UserWarning)
    g = nx.DiGraph()
    terminals = sorted(passage.layer(layer0.LAYER_ID).all, key=attrgetter("position"))
    g.add_nodes_from([(n.ID, {"label": '{0}\n{1}'.format(n.ID, n.text), "color": "white"}) for n in terminals])
    g.add_nodes_from([(n.ID, {"label": n.ID,
                              "color": "white"}) for n in passage.layer(layer1.LAYER_ID).all])
    g.add_edges_from([(n.ID, e.child.ID, {"label": "|".join(e.tags),
                                          "style": "dashed" if e.attrib.get("remote") else "solid"})
                      for layer in passage.layers for n in layer.all for e in n])
    pos = topological_layout_native(passage)
    nx.draw(g, pos, arrows=False, font_size=10,
            node_color=[d["color"] for _, d in g.nodes(data=True)],
            labels={n: d["label"] for n, d in g.nodes(data=True) if d["label"]},
            style=[d["style"] for _, _, d in g.edges(data=True)])
    nx.draw_networkx_edge_labels(g, pos, font_size=8,
                                 edge_labels={(u, v): d["label"] for u, v, d in g.edges(data=True)})

def topological_layout_native(passage):
    visited = defaultdict(set)
    pos = {}
    implicit_offset = 1 + max((n.position for n in passage.layer(layer0.LAYER_ID).all), default=-1)
    remaining = [n for layer in passage.layers for n in layer.all if not n.parents]
    while remaining:
        node = remaining.pop()
        if node.ID in pos:  # done already
            continue
        if node.children:
            children = [c for c in node.children if c.ID not in pos and c not in visited[node.ID]]
            if children:
                visited[node.ID].update(children)  # to avoid cycles
                remaining += [node] + children
                continue
            xs, ys = zip(*(pos[c.ID] for c in node.children))
            pos[node.ID] = (sum(xs) / len(xs), 1 + max(ys) ** 1.01)  # done with children
        elif node.layer.ID == layer0.LAYER_ID:  # terminal
            pos[node.ID] = (int(node.position), 0)
        else:  # implicit
            pos[node.ID] = (implicit_offset, 0)
            implicit_offset += 1
    return pos


def from_sentence_list(sentence_files, model_prefix, output_dir):

    from os.path import splitext
    from path_to_re.internal.tupa_parser import TupaParser

    parser = TupaParser(model_prefix)


    for sentence_file in sentence_files:

        with open(sentence_file, 'r') as file:
            sentence = file.read().replace('\n', '')
            parsed_passage = parser.parse_sentence(sentence)


        width = len(parsed_passage.terminals) * 19 / 27

        plt.figure(figsize=(width, width * 10 / 19))

        draw_from_re_representation(parsed_passage)

        filename, _ = splitext(sentence_file)

        plt.savefig(os.path.join(output_dir, filename + '.png'))
        plt.close()

def from_serialized_ucca_parsed_passage(re_representation_files, output_dir):

    from os.path import splitext


    for re_representation_file in re_representation_files:

        with open(re_representation_file, 'r') as file:
            serialization = file.read().replace('\n', '')
            parsed_passage = UccaParsedPassage.from_serialization(serialization)


        width = len(parsed_passage.terminals) * 19 / 27

        plt.figure(figsize=(width, width * 10 / 19))

        draw_from_re_representation(parsed_passage)

        filename, _ = splitext(re_representation_file)

        plt.savefig(os.path.join(output_dir, filename + '.png'))
        plt.close()

def draw_from_re_representation(passage):

    import matplotlib.cbook
    import networkx as nx
    warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
    warnings.filterwarnings("ignore", category=UserWarning)

    g = nx.DiGraph()

    g.add_nodes_from([(n.node_id, {"label": '{0}\n{1}'.format(n.node_id, n.text), "color": "white"}) for n in passage.terminals])
    g.add_nodes_from([(n.node_id, {"label": n.node_id, "color": "white"}) for n in passage.non_terminals])

    g.add_edges_from([(edge.parent.node_id,
                       edge.child.node_id,
                       {"label": edge.tag, "style": "solid" if edge.classification == 'direct' else "dashed"})
        for edge in passage.edges])

    pos = topological_layout_re(passage)

    nx.draw(g, pos, arrows=False, font_size=10,
            node_color=[d["color"] for _, d in g.nodes(data=True)],
            labels={n: d["label"] for n, d in g.nodes(data=True) if d["label"]})

    nx.draw_networkx_edge_labels(g, pos, font_size=8,
                                 edge_labels={(u, v): d["label"] for u, v, d in g.edges(data=True)})

def topological_layout_re(passage):


    nodes_to_parents = passage.get_ucca_nodes_with_parents()
    nodes_to_children = passage.get_ucca_nodes_with_children()



    visited = defaultdict(set)
    pos = {}
    remaining = [node for node, parents in nodes_to_parents.items() if len(parents) is 0]
    implicit_offset = 1 + max((n.token_id for n in passage.terminals), default=-1)


    while remaining:
        node = remaining.pop()

        if node.node_id in pos:  # done already
            continue


        if len(nodes_to_children[node]) > 0:
            children = [c for c in nodes_to_children[node] if c.node_id not in pos and c not in visited[node.node_id]]
            if len(children) > 0:
                visited[node.node_id].update(children)  # to avoid cycles
                remaining += [node] + children
                continue

            xs, ys = zip(*(pos[c.node_id] for c in nodes_to_children[node]))

            pos[node.node_id] = (sum(xs) / len(xs), 1 + max(ys) ** 1.01)  # done with children

        elif isinstance(node, UccaTerminalNode):  # terminal
            pos[node.node_id] = (node.token_id, 0)

        else:  # implicit
            pos[node.node_id] = (implicit_offset, 0)
            implicit_offset += 1

    return pos










if __name__ == "__main__":
    args = docopt(__doc__)

    no_serialization = args.get('raw', False)
    xml_serialization = args.get('xml_serializion', False)
    my_serialization = args.get('my_serialization', False)

    input_file = args.get('<input-file>', None)
    output_dir = args.get('<output-dir>', None)

    tupa_module_path = args.get('<tupa_module_path>', None)

    os.makedirs(output_dir, exist_ok=True)
    matplotlib.use('Agg')

    if xml_serialization:
        from_xml([input_file], output_dir)

    elif my_serialization:
        from_serialized_ucca_parsed_passage([input_file], output_dir)

    elif no_serialization:
        from_sentence_list([input_file], tupa_module_path, output_dir)