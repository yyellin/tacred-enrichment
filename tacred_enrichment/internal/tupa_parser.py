import os
import sys
from collections import OrderedDict

import networkx
from tupa.parse import Parser
from ucca.convert import from_text
from ucca.core import Passage
from ucca.layer0 import Layer0
from ucca.layer1 import Layer1
from ucca.textutil import annotate_all

from tacred_enrichment.internal.ucca_types import UccaParsedPassage, UccaEdge, UccaNode, UccaTerminalNode


class TupaParser(object):
    """

    Attributes
    ----------
    Methods
    -------

    """

    # the 'from_text' method requires a passage id, however users of this class will not need it.
    # thus, we'll just provide a arbitrary id, in the form of a class level counter that gets
    # incremented after each use
    __passage_counter = 0

    def __init__(self, model_prefix):
        """

        Parameters
        ----------
        """

        # the sys.argv assignment is a necessary: without it tupa.parse.Parser will throw exceptions
        remember_argv = sys.argv
        sys.argv = ['-m', model_prefix]

        parser = Parser(model_files= model_prefix)
        parser.models[0].load()
        parser.trained = True

        self.__parser = parser

        # Since 'parse_sentence' calls 'annotate_all' which lazily instantiated a spacey pipeline,
        # and since we want all the initialization to occur in the __init__ method, we simply call
        # 'parse_sentence' with dummy input
        self.parse_sentence('Hello dummy world')

        # undo hack side effect
        sys.argv = remember_argv

    def parse_sentence(self, sentence):

        reg_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w', encoding='UTF-8')
        parsed_passage = None

        try:
            TupaParser.__passage_counter =+ 1
            passage_id = TupaParser.__passage_counter =+ 1

            # from_text will convert the sentence into a ucca structure.
            # annotate_all will annotate the structure with information from the Spacy parse.
            # annotate_all returns a generator - one that will yield only one object - hence
            # we call next
            unparsed_passage = next( annotate_all( from_text( sentence, passage_id, one_per_line= True) ) )


            # The 'tupa.parse class's parse method expects a list of unparsed-message. We also need to set
            # the 'evaluate' argument to True, otherwise we get incorrect results. (Ofir Arviv advised as such).
            # The parse method also returns a generator, hence the need to call next.
            # The actual object returned is a tuple of the parsed-passage and an internal score object. We're
            # not interested in the score though, so we just extract the parsed-passage
            parsed_passage_and_score = next( self.__parser.parse( [unparsed_passage], evaluate=True) )
            internal_parsed_passage = parsed_passage_and_score[0]
            parsed_passage = TupaParser.__get_ucca_parsed_passage_from_passage(internal_parsed_passage)

        finally:
            sys.stdout = reg_stdout
            return parsed_passage

    def parse_sentences(self, sentences):

        reg_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w', encoding='UTF-8')
        parsed_passages = []

        try:

            unparsed_passages = []
            for sentence in sentences:

                TupaParser.__passage_counter =+ 1
                passage_id = TupaParser.__passage_counter =+ 1

                # from_text will convert the sentence into a ucca structure.
                # annotate_all will annotate the structure with information from the Spacy parse.
                # annotate_all returns a generator - one that will yield only one object - hence
                # we call next
                unparsed_passage = next( annotate_all( from_text( sentence, passage_id, one_per_line= True) ) )
                unparsed_passages.append(unparsed_passage)


            # We also need to set the 'evaluate' argument to True, otherwise we get incorrect results.
            # (Ofir Arviv advised as such).
            # The parse method also returns a generator, hence the need to call next.
            # The actual object returned is a tuple of the parsed-passage and an internal score object. We're
            # not interested in the score though, so we just extract the parsed-passage
            for parsed_passage_and_score in self.__parser.parse( unparsed_passages, evaluate=True):
                internal_parsed_passage = parsed_passage_and_score[0]
                parsed_passage = TupaParser.__get_ucca_parsed_passage_from_passage(internal_parsed_passage)
                parsed_passages.append(parsed_passage)

        finally:
            sys.stdout = reg_stdout
            return parsed_passages


    @staticmethod
    def __get_ucca_parsed_passage_from_passage(passage: Passage):
        ucca_parsed_passage = UccaParsedPassage(passage)

        ucca_parsed_passage.terminals = []
        ucca_parsed_passage.non_terminals = []
        ucca_parsed_passage.edges = []

        ucca_node_lookup = {}

        layer0 = next(layer for layer in passage.layers if isinstance(layer, Layer0))
        layer1 = next(layer for layer in passage.layers if isinstance(layer, Layer1))

        for node in layer0.all:
            edge_tags_in = [edge.tag for edge in node.incoming]
            token_id = int(node.ID.split('.')[1])  # :)
            lemma, tag, pos, ent, head =  node.extra['lemma'], node.extra['tag'], node.extra['pos'], node.extra['ent_type'], node.extra['head']
            terminal_node = UccaTerminalNode(node.ID, edge_tags_in, token_id, node.text, lemma, tag, pos, ent, head)
            ucca_parsed_passage.terminals.append(terminal_node)
            ucca_node_lookup[node.ID] = terminal_node

        for node in layer1.all:
            edge_tags_in = [edge.tag for edge in node.incoming]
            non_terminal_node = UccaNode(node.ID, edge_tags_in)
            ucca_parsed_passage.non_terminals.append(non_terminal_node)
            ucca_node_lookup[node.ID] = non_terminal_node

        # all the edges are from layer1 nodes to their children (which can include layer0
        # nodes)

        edge_lookup = OrderedDict()


        for node in layer1.all:
            for edge in node.outgoing:
                child_node = ucca_node_lookup[edge.child.ID]
                parent_node = ucca_node_lookup[edge.parent.ID]

                ucca_edge = UccaEdge(child_node, parent_node, edge.tag, 'remote' if edge.attrib.get('remote') else 'direct')
                edge_lookup[(edge.parent.ID, edge.child.ID)] = ucca_edge

                #ucca_parsed_passage.edges.append(UccaEdge(child_node, parent_node, edge.tag, 'remote' if edge.attrib.get('remote') else 'direct'))


        # the edges as extracted in the sequence above are not in proper order - specifically children of
        # a given parent are not in the order appropriate to the actual terminals ...

        # the following code fixes this up by sorting children based on their earliest direct terminal descendant

        # we'll first create a DiGraph with all the edges - this DiGraph will allow us to easily iterate over the edges
        # in breadth first fashion (something we couldn't do by just considering the edge list)
        digraph_with_remotes = networkx.DiGraph(list(edge_lookup.keys()))

        # and then a DiGraph without remote edges - we'll use this for  sorting
        digraph_without_remotes = networkx.DiGraph( [ edge_key for edge_key, edge in edge_lookup.items() if edge.classification == 'direct' ] )

        # there might be a better way for finding the root of the dag; i didn't find one
        root = next(networkx.topological_sort(digraph_with_remotes))

        # standard stack based implementation for iterating over the dag in breadth first fashion
        stack = [ root ]

        while stack:
            node = stack.pop()

            # get all the nodes children
            children = list(digraph_with_remotes.successors(node))

            # no need to sort if there is just one child
            if len(children) > 1:

                # child_to_lowest_value_terminal will contain a mapping if each of nodes' childlren to
                # their respective earliest terminal that it's directly connected to
                child_to_lowest_value_terminal = {}
                for child in children:

                    # in the case of a non-terminal ...
                    if child.split('.')[0] == '1':
                        # only consider direct descendants (that's why we call networkx.descendants on 'digraph_without_remotes'
                        # and not on 'digraph_with_remotes'
                        descendants = networkx.descendants(digraph_without_remotes, child)

                        # terminal descendants all have ids with a '0.x' format, where x is an integer that reflects the token
                        # index of the terminal
                        terminal_descendants = [ int(descendant.split('.')[1]) for descendant in descendants if descendant.split('.')[0] == '0' ]

                        # get the earliest terminal id for child by sorting it terminal descendants and then
                        # picking the first one
                        terminal_descendants.sort()
                        earliest_terminal_id = terminal_descendants[0]

                    else:
                        #'child' is a terminal, so it's 'earliest_terminal_id' is basically itself ..
                        earliest_terminal_id = int(child.split('.')[1])

                    child_to_lowest_value_terminal[child] = earliest_terminal_id

                # finally sort the children based on their earliest terminal id
                children = [child for child, _ in sorted( child_to_lowest_value_terminal.items(), key=lambda x: x[1] ) ]

            # now we can add edges in proper order
            for child_node in children:
                edge = edge_lookup[(node, child_node)]
                ucca_parsed_passage.edges.append(edge)

            # we are popping from a stack so in order to treat the children in their proper
            # order we need to push them to stack in reverse order
            children.reverse()
            stack += children




        return ucca_parsed_passage
