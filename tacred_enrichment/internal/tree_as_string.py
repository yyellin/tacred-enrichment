'''
Copied from https://rosettacode.org/wiki/Visualize_a_tree#Vertically_centered_parents with some minor changes
to function names

Textually visualized tree, with vertically-centered parent nodes
Tree style and algorithm inspired by the Haskell snippet at: https://doisinkidney.com/snippets/drawing-trees.html

'''

from functools import reduce
from itertools import (chain, takewhile)




# compose (<<<) :: (b -> c) -> (a -> b) -> a -> c
def _compose(g):
    '''Right to left function composition.'''
    return lambda f: lambda x: g(f(x))


# concatMap :: (a -> [b]) -> [a] -> [b]
def _concat_map(f):
    '''A concatenated list over which a function has been mapped.
       The list monad can be derived by using a function f which
       wraps its output in a list,
       (using an empty list to represent computational failure).
    '''
    return lambda xs: list(
        chain.from_iterable(map(f, xs))
    )


# fmapTree :: (a -> b) -> Tree a -> Tree b
def _fmap_tree(f):
    '''A new tree holding the results of
       applying f to each root in
       the existing tree.
    '''

    def go(x):
        return node_constructor(f(x['root']))(
            [go(v) for v in x['nest']]
        )

    return lambda tree: go(tree)


# foldr :: (a -> b -> b) -> b -> [a] -> b
def _foldr(f):
    '''Right to left reduction of a list,
       using the binary operator f, and
       starting with an initial accumulator value.
    '''

    def g(x, a):
        return f(a, x)

    return lambda acc: lambda xs: reduce(
        g, xs[::-1], acc
    )


# intercalate :: [a] -> [[a]] -> [a]
# intercalate :: String -> [String] -> String
def intercalate(x):
    '''The concatenation of xs
       interspersed with copies of x.
    '''
    return lambda xs: x.join(xs) if isinstance(x, str) else list(
        chain.from_iterable(
            reduce(lambda a, v: a + [x, v], xs[1:], [xs[0]])
        )
    ) if xs else []


# iterate :: (a -> a) -> a -> Gen [a]
def _iterate(f):
    '''An infinite list of repeated
       applications of f to x.
    '''

    def go(x):
        v = x
        while True:
            yield v
            v = f(v)

    return lambda x: go(x)


# levels :: Tree a -> [[a]]
def _levels(tree):
    '''A list of the nodes at each level of the tree.'''
    return list(
        _map(_map(_root))(
            takewhile(
                bool,
                _iterate(_concat_map(_nest))(
                    [tree]
                )
            )
        )
    )


# map :: (a -> b) -> [a] -> [b]
def _map(f):
    '''The list obtained by applying f
       to each element of xs.
    '''
    return lambda xs: list(map(f, xs))


# nest :: Tree a -> [Tree a]
def _nest(t):
    '''Accessor function for children of tree node.'''
    return t['nest'] if 'nest' in t else None


# root :: Tree a -> a
def _root(t):
    '''Accessor function for data of tree node.'''
    return t['root'] if 'root' in t else None


# node :: a -> [Tree a] -> Tree a
def node_constructor(v):
    '''Contructor for a Tree node which connects a
       value of some kind to a list of zero or
       more child trees.
    '''
    return lambda xs: { 'root': v, 'nest': xs}


# draw_tree :: Bool -> Bool -> Tree a -> String
def draw_tree(blnCompact):
    '''Monospaced UTF8 left-to-right text tree in a
       compact or expanded format, with any lines
       containing no nodes optionally pruned out.
    '''

    def go(blnPruned, tree):
        # measured :: a -> (Int, String)
        def measured(x):
            '''Value of a tree node
               tupled with string length.
            '''
            s = ' ' + str(x) + ' '
            return len(s), s

        # lmrFromStrings :: [String] -> ([String], String, [String])
        def lmrFromStrings(xs):
            '''Lefts, Mid, Rights.'''
            i = len(xs) // 2
            ls, rs = xs[0:i], xs[i:]
            return ls, rs[0], rs[1:]

        # stringsFromLMR :: ([String], String, [String]) -> [String]
        def stringsFromLMR(lmr):
            ls, m, rs = lmr
            return ls + [m] + rs

        # fghOverLMR
        # :: (String -> String)
        # -> (String -> String)
        # -> (String -> String)
        # -> ([String], String, [String])
        # -> ([String], String, [String])
        def fghOverLMR(f, g, h):
            def go(lmr):
                ls, m, rs = lmr
                return (
                    [f(x) for x in ls],
                    g(m),
                    [h(x) for x in rs]
                )

            return lambda lmr: go(lmr)

        # leftPad :: Int -> String -> String
        def leftPad(n):
            return lambda s: (' ' * n) + s

        # treeFix :: (Char, Char, Char) -> ([String], String, [String])
        #                               ->  [String]
        def treeFix(l, m, r):
            def cfix(x):
                return lambda xs: x + xs

            return _compose(stringsFromLMR)(
                fghOverLMR(cfix(l), cfix(m), cfix(r))
            )

        def lmrBuild(w, f):
            def go(wsTree):
                nChars, x = wsTree['root']
                _x = ('─' * (w - nChars)) + x
                xs = wsTree['nest']
                lng = len(xs)

                # linked :: String -> String
                def linked(s):
                    c = s[0]
                    t = s[1:]
                    return _x + '┬' + t if '┌' == c else (
                        _x + '┤' + t if '│' == c else (
                            _x + '┼' + t if '├' == c else (
                                    _x + '┴' + t
                            )
                        )
                    )

                # LEAF ------------------------------------
                if 0 == lng:
                    return ([], _x, [])

                # SINGLE CHILD ----------------------------
                elif 1 == lng:
                    def lineLinked(z):
                        return _x + '─' + z

                    rightAligned = leftPad(1 + w)
                    return fghOverLMR(
                        rightAligned,
                        lineLinked,
                        rightAligned
                    )(f(xs[0]))

                # CHILDREN --------------------------------
                else:
                    rightAligned = leftPad(w)
                    lmrs = [f(x) for x in xs]
                    return fghOverLMR(
                        rightAligned,
                        linked,
                        rightAligned
                    )(
                        lmrFromStrings(
                            intercalate([] if blnCompact else ['│'])(
                                [treeFix(' ', '┌', '│')(lmrs[0])] + [
                                    treeFix('│', '├', '│')(x) for x
                                    in lmrs[1:-1]
                                ] + [treeFix('│', '└', ' ')(lmrs[-1])]
                            )
                        )
                    )

            return lambda wsTree: go(wsTree)

        measuredTree = _fmap_tree(measured)(tree)
        levelWidths = reduce(
            lambda a, xs: a + [max(x[0] for x in xs)],
            _levels(measuredTree),
            []
        )
        treeLines = stringsFromLMR(
            _foldr(lmrBuild)(None)(levelWidths)(
                measuredTree
            )
        )
        return [
            s for s in treeLines
            if any(c not in '│ ' for c in s)
        ] if (not blnCompact and blnPruned) else treeLines

    return lambda blnPruned: (
        lambda tree: '\n'.join(go(blnPruned, tree))
    )




def example():
    '''Trees drawn in varying formats'''

    # tree1 :: Tree Int
    tree1 = node_constructor(1)([
        node_constructor(2)([
            node_constructor(4)([
                node_constructor(7)([])
            ]),
            node_constructor(5)([])
        ]),
        node_constructor(3)([
            node_constructor(6)([
                node_constructor(8)([]),
                node_constructor(9)([])
            ])
        ])
    ])

    # tree :: Tree String
    tree2 = node_constructor('Alpha')([
        node_constructor('Beta')([
            node_constructor('Epsilon')([]),
            node_constructor('Zeta')([]),
            node_constructor('Eta')([]),
            node_constructor('Theta')([
                node_constructor('Mu')([]),
                node_constructor('Nu')([])
            ])
        ]),
        node_constructor('Gamma')([
            node_constructor('Xi')([node_constructor('Omicron')([])])
        ]),
        node_constructor('Delta')([
            node_constructor('Iota')([]),
            node_constructor('Kappa')([]),
            node_constructor('Lambda')([])
        ])
    ])

    print(
        '\n\n'.join([
            'Fully compacted (parents not all centered):',
            draw_tree(True)(False)(
                tree1
            ),
            'Expanded with vertically centered parents:',
            draw_tree(False)(False)(
                tree2
            ),
            'Centered parents with nodeless lines pruned out:',
            draw_tree(False)(True)(
                tree2
            )
        ])
    )






