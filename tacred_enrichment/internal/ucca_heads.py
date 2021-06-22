from internal.ucca_enhancer import UccaEnhancer
from tacred_enrichment.internal.ucca_types import UccaParsedPassage
from semstr.convert import to_conllu
from conllu import parse as conllu_parse


class UccaHeads(UccaEnhancer):

    def enhance(self, tac, tac_to_ucca, ucca: UccaParsedPassage):

        lines_representation = to_conllu(ucca.native)
        conllu = conllu_parse('\n'.join(lines_representation))

        ucca_heads = [token_info['head'] for i, token_info in enumerate(conllu[0])]
        ucca_deps = [token_info['deps'] for i, token_info in enumerate(conllu[0])]

        return {'ucca_heads': ucca_heads, 'ucca_deps': ucca_deps}
