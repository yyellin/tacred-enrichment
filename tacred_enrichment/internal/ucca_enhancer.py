from tacred_enrichment.internal.ucca_types import UccaParsedPassage

class UccaEnhancer(object):
    def enhance(self, tac, tac_to_ucca, ucca: UccaParsedPassage):
        raise NotImplementedError('subclasses must override enhance()!')