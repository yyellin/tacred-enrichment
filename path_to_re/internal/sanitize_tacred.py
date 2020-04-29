class SanitizeTacred(object):
    """

    """
    __replace = { '-LRB-': '(', '-RRB-': ')', '``': '"', '\'\'': '"', '--': '-' }

    @staticmethod
    def sanitize_tokens(tacred_tokens):
        return  [SanitizeTacred.__replace[tac_token] if tac_token in SanitizeTacred.__replace else tac_token for tac_token in tacred_tokens]
