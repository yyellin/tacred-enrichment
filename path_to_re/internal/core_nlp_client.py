import requests
import json
from stanfordcorenlp import StanfordCoreNLP


class CoreNlpClient(StanfordCoreNLP):
    """
      IndependentStanfordCoreNLP wraps the 'StanfordCoreNLP' from the Lynten/stanford-corenlp package
      with the purpose of:
      1. providing a constructor that defaults to an external java Core NLP server
      2. providing an 'all_i_ever_wanted' method for extracting only the fields we're inerteres in.
      """

    def __init__(self, host, port, timeout):
        StanfordCoreNLP.__init__(self, path_or_host='http://{}'.format(host), port=port, timeout=timeout)

        # in case the server is still cold, let's warm it up
        self.get_deps("Let's get started here")

    def get_deps(self, sentences):
        sentences = sentences.encode('utf-8')

        properties = {
            'annotators': 'lemma, depparse',
            'ssplit.eolonly': 'true',
            'outputFormat': 'json'
        }

        params = {'properties': str(properties), 'pipelineLanguage': self.lang}

        r = requests.post(self.url, params=params, data=sentences)
        r_dict = json.loads(r.text)

        return r_dict


    def get_ner(self, sentences):
        sentences = sentences.encode('utf-8')

        properties = {
            'annotators': 'ner',
            'ssplit.eolonly': 'true',
            'outputFormat': 'json'
        }

        params = {'properties': str(properties), 'pipelineLanguage': self.lang}

        r = requests.post(self.url, params=params, data=sentences)
        r_dict = json.loads(r.text)

        return r_dict