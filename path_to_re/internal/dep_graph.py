from collections import namedtuple, defaultdict
from copy import deepcopy


import networkx


class Step(namedtuple('Step', 'me, next, dep_direction, dependency')):
    """
    'Step' represents a single step in the path between a current node in a dependency tree
    and the next node in the path.
    If the direction corresponds to an edge from a node to it's parent it will be indicated
    with the '↑' character; if it's from the parent of the node to the node itself the direction
    will be indicated with the '↓' symbol
    """

    @staticmethod
    def get_default_representation(steps):
        """
        'get_default_representation' will take a list of Step objects and return
        a default representation for them

        Parameters
        ----------
        steps :
            list of 'step' objects

        Returns
        -------
            string representation of step objects

        """

        return ' '.join(['{0}{1}'.format(step.dep_direction, step.dependency) for step in steps])


    @staticmethod
    def get_dependency_representation(steps):
        """

        Parameters
        ----------
        steps :
            list of 'step' objects

        Returns
        -------
            string representation of dependencies

        """

        return ''.join([step.dependency for step in steps])


class DepGraph(object):
    """
    'DepGraph' is initialized with a list of Link objects to represent a dag.
    Each edge in the dag is represented by an Edge object.

    Attributes
    ----------
    __edge_to_link
        maps each edge in the dependency tree (from a node to its parent) to its link

    __graph
        a networkx.Graph non directed tree which will be used, for example, to calculate the shortest path between nodes

    __digraph
        a networkx.DiGraph directed tree which will be used, for example, to produce lowest common ancestor


    Methods
    -------
    get_steps
        Returns the shortest path between a start and end word represented as a deserialization of a
        list of Step objects, without consideration to direction of the edge.

    """

    class Edge(namedtuple('Edge', 'parent, me')):
        """
        As its name suggests the 'Edge' object represents an edge between a node in the dependency tree
        and its parent.
        As Edge is essentially a tuple, it can be used to instantiate networkx.Graph objects
        """

    def __init__(self, links, is_terminal = lambda x: True):
        """

        Parameters
        ----------
        links :
           list of 'Link' objects that represent a dependency parse
        """

        self.__edge_to_link = {}

        for link in links:
            # convert a link to an edge object that networkx.Graph can be
            # initialized with
            edge = DepGraph.Edge(parent=link.parent_index, me=link.word_index)
            self.__edge_to_link[edge] = link


        self.__digraph = networkx.DiGraph(list(self.__edge_to_link.keys()))

        # we'll initialize __graph lazily
        self.__graph = None

        #
        self.__is_terminal = is_terminal

    def root(self):
        """
        Return root node_index

        """


        # there might be a better way for finding the root of the dag; i didn't find one
        root = next(networkx.topological_sort(self.__digraph))

        return root

    def get_terminals(self):
        """

        Returns
        -------
        The ids  of all terminals

        """
        terminals = set()
        for link in self.__edge_to_link.values():
            if self.__is_terminal(link.word_index):
                terminals.add(link.word_index)

        return list(terminals)






    def successors(self, node_index):
        """
        Simple wrapper method over DiGraph's 'successors' method ..

        """
        return self.__digraph.successors(node_index)

    def get_parents(self, id):
        """

        Parameters
        ----------
        id
            id of node for whose parents we're looking for

        Returns
        -------
        The ids  of all parents of the node whose id was give

        """

        return networkx.ancestors(self.__digraph, source=id, )

    def get_undirected_steps(self, start, end):
        """

        Parameters
        ----------
        start
            first node in path
        end
            last node in path

        Returns
        -------
        The shortest path between 'start and 'end' represented as a deserialization of a
        list of Step objects
        """
        if self.__graph is None:
            self.__graph = networkx.Graph(list(self.__edge_to_link.keys()))


        node_list = networkx.shortest_path(self.__graph, source=start, target=end)
        steps = []

        for i in range(0, len(node_list) - 1):

            me = node_list[i]
            next = node_list[i + 1]

            if DepGraph.Edge(me, next) in self.__edge_to_link:
                edge = DepGraph.Edge(me, next)
                direction = '>'  # '↑'
            else:
                # If the edge represented by (this, next) does not exist in the
                # '__edge_to_deptype' map, it means that the actual edge in the
                # dependency parse is from next to this, where this is the parent.
                # Thus we switch the order ...
                edge = DepGraph.Edge(next, me)
                direction = '<'  # ''↓'

            dependency = self.__edge_to_link[edge].dep_type

            step = Step(me=me, next=next, dep_direction=direction, dependency=dependency)

            steps.append(step)
            # ' '.join(['{0}{1}'.format(step.direction, step.dependency) for step in steps])

        return steps

    def get_links_of_lca_subgraph(self, one, another):
        """

        Parameters
        ----------
        one
            one node in the tree
        another
            a second node in the tree

        Returns
        -------
        The all the links corresponding to the smallest sub-graph containing nodes one and two,
        in DFS order
        """

        lowest_common_ancestor = networkx.lowest_common_ancestor(self.__digraph, one, another)

        links = []
        to_visit = [(None,lowest_common_ancestor)]

        while to_visit:
            parent_node, current_node = to_visit.pop()

            if parent_node != None:
                link = deepcopy(self.__edge_to_link[(parent_node, current_node)])
                links.append(link)

            for child_node in self.__digraph.successors(current_node):
                to_visit.insert(0, (current_node, child_node) )




        # subgraph = networkx.ego_graph( self.__digraph, lowest_common_ancestor, 1000)
        # for edge in  networkx.dfs_edges(subgraph):
        #     link = deepcopy(self.__edge_to_link[edge])
        #     links.append(link)

        return links


    def get_minimal_subgraph(self, one, another, compare_by):
        """

        Parameters
        ----------
        one
            one node in the tree
        another
            a second node in the tree

        Returns
        -------
        """

        ancestors_one = networkx.ancestors(self.__digraph, one )
        ancestors_another = networkx.ancestors(self.__digraph,another)

        common_ancestors  = set(ancestors_one).intersection(ancestors_another)

        common_ancestor_to_subtrees = {}
        for common_ancestor in common_ancestors:

            links = []
            to_visit = [(None,common_ancestor)]

            while to_visit:
                parent_node, current_node = to_visit.pop()

                if parent_node != None:
                    link = deepcopy(self.__edge_to_link[(parent_node, current_node)])
                    links.append(link)

                for child_node in self.__digraph.successors(current_node):
                    to_visit.insert(0, (current_node, child_node) )

            subtree = DepGraph(links, self.__is_terminal)
#            terminals = subtree.get_terminals()

            common_ancestor_to_subtrees[common_ancestor] = subtree

        sorted_subtrees = sorted(common_ancestor_to_subtrees.values(),key = lambda l : compare_by(l.get_terminals(),one,another))

        if len(sorted_subtrees) > 0:
            return sorted_subtrees[0]

        else:
            return None



