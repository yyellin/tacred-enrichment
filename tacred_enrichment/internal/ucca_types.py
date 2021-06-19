import json
from itertools import chain

from tacred_enrichment.internal.link import Link


class UccaNode(object):
    def __init__(self, node_id, edge_tags_in):
        self.node_id = node_id
        self.edge_tags_in = [x for i, x in enumerate(edge_tags_in) if edge_tags_in.index(x) == i]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.node_id == other.node_id
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.node_id)

    def __str__(self):
        return self.node_id


class UccaTerminalNode(UccaNode):
    def __init__(self, node_id, edge_tags_in, token_id, text, lemma, tag=None, pos=None, ent=None, head=None):
        super().__init__(node_id, edge_tags_in)

        self.token_id = token_id
        self.text = text
        self.lemma = lemma
        self.tag = tag
        self.pos = pos
        self.ent = ent
        self.head = head


class UccaEdge(object):
    def __init__(self, child, parent, tag, classification):
        self.child = child
        self.parent = parent
        self.tag = tag
        self.classification = classification

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.child.node_id == other.child.node_id and self.parent.node_id == other.parent.node_id \
                   and self.tag == other.tag and self.classification == other.classification
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.child.node_id, self.parent.node_id))

    def get_representations(self):
        if len(self.parent.edge_tags_in) == 0:
            return '{}.'.format(self.tag)

        return ['{}{}'.format(self.tag, parent_edge_tag_in) for parent_edge_tag_in in self.parent.edge_tags_in]


class UccaParsedPassage(object):
    class UccaParsedPassageEncoding(json.JSONEncoder):

        def default(self, z):

            if isinstance(z, UccaTerminalNode):
                return (z.node_id, z.token_id, z.text, z.lemma, z.tag, z.pos, z.ent, z.ud_head)

            elif isinstance(z, UccaNode):
                return (z.node_id, z.edge_tags_in)

            elif isinstance(z, UccaEdge):
                return (z.child.node_id, z.parent.node_id, z.tag, z.classification)

            elif isinstance(z, UccaParsedPassage):
                data = {}
                data['terminals'] = z.terminals
                data['non_terminals'] = z.non_terminals
                data['edges'] = z.edges
                return data

            else:
                return super().default(z)

    def __init__(self, native=None):
        self.native = native

    def serialize(self):
        return json.dumps(self, cls=UccaParsedPassage.UccaParsedPassageEncoding)

    def get_ucca_nodes_with_children(self):

        node_to_children = {}
        for node in chain(self.terminals, self.non_terminals):
            node_to_children[node] = []

        for edge in self.edges:
            parent = self.get_ucca_node_by_node_id(edge.parent.node_id)
            child = self.get_ucca_node_by_node_id(edge.child.node_id)

            node_to_children[parent].append(child)

        return node_to_children

    def get_ucca_nodes_with_parents(self):

        node_to_parents = {}
        for node in chain(self.terminals, self.non_terminals):
            node_to_parents[node] = []


        for edge in self.edges:

            child = self.get_ucca_node_by_node_id(edge.child.node_id)
            parent = self.get_ucca_node_by_node_id(edge.parent.node_id)

            node_to_parents[child].append(parent)

        return node_to_parents

    def get_ucca_node_by_node_id(self, node_id):
        return next(node for node in chain(self.terminals, self.non_terminals) if node.node_id == node_id)

    def get_node_id_by_token_id(self, token_id):
        return next(terminal.node_id for terminal in self.terminals if terminal.token_id == token_id)

    def get_links(self):
        """
        'get_links' will return a list of 'Link' objects representing the UccaParsedPassage object

        Parameters
        ----------

        Returns
        -------
            List of Link objects representing the UccaParsedPassage

        """

        links = []

        for edge in self.edges:
            link = Link(word=edge.child.text if isinstance(edge.child, UccaTerminalNode) else None,
                        word_index=edge.child.node_id,
                        parent=None,
                        parent_index=edge.parent.node_id,
                        dep_type=edge.tag)

            links.append(link)

        return links

    def get_path_representations(self, steps, mark_peak=False):

        class StringReference(object):
            def __init__(self, string):
                self.string = string

        in_progress_list = [StringReference('')]

        previous_direction = ''
        for step in steps:

            # we ave flipped direction from up to down
            if mark_peak and previous_direction == '!' and step.dep_direction == '^':
                peak = self.get_ucca_node_by_node_id(step.me)

                # using '0' to indicate edges in of the root
                peak_edges_in = peak.edge_tags_in if len(peak.edge_tags_in) > 0 else ['0']

                new_in_progress_list = []
                for edge_tag_in in peak_edges_in:
                    for in_progress in in_progress_list:
                        in_progress.string += '{} '.format(edge_tag_in)
                        new_in_progress_list.append(in_progress)
                in_progress_list = new_in_progress_list

            for in_progress in in_progress_list:
                in_progress.string += '{0}{1} '.format(step.dep_direction, step.dependency)

            previous_direction = step.dep_direction

        # return representations making sure to remove last whitespace
        path_representations = [path_representation.string[:-1] for path_representation in in_progress_list]
        return path_representations



    @staticmethod
    def from_serialization(serialization: str):

        self = UccaParsedPassage()

        self.terminals = []
        self.non_terminals = []
        self.edges = []

        #edge_lookup = OrderedDict()

        try:
            representation = eval(serialization)

            for element in representation['terminals']:
                terminal = UccaTerminalNode(element[0],
                                            ['Terminal'],
                                            element[1],
                                            element[2],
                                            element[3],
                                            element[4],
                                            element[5])
                self.terminals.append(terminal)

            for element in representation['non_terminals']:
                non_terminal = UccaNode(element[0], element[1])
                self.non_terminals.append(non_terminal)

            for element in representation['edges']:
                child_id = element[0]
                parent_id = element[1]
                edge_tag = element[2]
                classification = element[3]

                child = next(node for node in chain(self.non_terminals, self.terminals) if node.node_id == child_id)
                parent = next(node for node in chain(self.non_terminals, self.terminals) if node.node_id == parent_id)

                self.edges.append(UccaEdge(child, parent, edge_tag, classification))
                #edge_lookup[(parent_id, child_id)] = UccaEdge(child, parent, edge_tag, classification)

        except:
            return None


        # # the edges in the serialization are not in proper order - specifically children of a given parent are not
        # # in the order appropriate to the actual terminals ...
        #
        # # the following sequence fixes this up by sorting children based on their earliest direct terminal descendant
        #
        # # we'll first create a DiGraph with all the edges - this DiGraph will allow us to easily iterate over the edges
        # # in breadth first fashion (something we couldn't do by just considering the edge list)
        # digraph_with_remotes = networkx.DiGraph(list(edge_lookup.keys()))
        #
        # # and then a DiGraph without remote edges - we'll use this for  sorting
        # digraph_without_remotes = networkx.DiGraph( [ edge_key for edge_key, edge in edge_lookup.items() if edge.classification == 'direct' ] )
        #
        # # there might be a better way for finding the root of the dag; i didn't find one
        # root = next(networkx.topological_sort(digraph_with_remotes))
        #
        # # standard stack based implementation for iterating over the dag in breadth first fashion
        # stack = [ root ]
        #
        # while stack:
        #     node = stack.pop()
        #
        #     # get all the nodes children
        #     children = list(digraph_with_remotes.successors(node))
        #
        #     # no need to sort if there is just one child
        #     if len(children) > 1:
        #
        #         # child_to_lowest_value_terminal will contain a mapping if each of nodes' childlren to
        #         # their respective earliest terminal that it's directly connected to
        #         child_to_lowest_value_terminal = {}
        #         for child in children:
        #
        #             # in the case of a non-terminal ...
        #             if child.split('.')[0] == '1':
        #                 # only consider direct descendants (that's why we call networkx.descendants on 'digraph_without_remotes'
        #                 # and not on 'digraph_with_remotes'
        #                 descendants = networkx.descendants(digraph_without_remotes, child)
        #
        #                 # terminal descendants all have ids with a '0.x' format, where x is an integer that reflects the token
        #                 # index of the terminal
        #                 terminal_descendants = [ int(descendant.split('.')[1]) for descendant in descendants if descendant.split('.')[0] == '0' ]
        #
        #                 # get the earliest terminal id for child by sorting it terminal descendants and then
        #                 # picking the first one
        #                 terminal_descendants.sort()
        #                 earliest_terminal_id = terminal_descendants[0]
        #
        #             else:
        #                 #'child' is a terminal, so it's 'earliest_terminal_id' is basically itself ..
        #                 earliest_terminal_id = int(child.split('.')[1])
        #
        #             child_to_lowest_value_terminal[child] = earliest_terminal_id
        #
        #         # finally sort the children based on their earliest terminal id
        #         children = [child for child, _ in sorted( child_to_lowest_value_terminal.items(), key=lambda x: x[1] ) ]
        #
        #     # now we can add edges in proper order
        #     for child_node in children:
        #         edge = edge_lookup[(node, child_node)]
        #         self.edges.append( edge )
        #
        #     # we are popping from a stack so in order to treat the children in their proper
        #     # order we need to push them to stack in reverse order
        #     children.reverse()
        #     stack += children



        return self


def is_terminal(index):
    return index.startswith('0.')
