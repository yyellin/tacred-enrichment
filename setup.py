from setuptools import setup

setup(
    name='tacred_enrichment',
    version='1.0.0',
    packages=['tacred_enrichment', 'tacred_enrichment.extra', 'tacred_enrichment.internal', 'tacred_enrichment.gcn', 'tacred_enrichment.gcn.supplement', 'tacred_enrichment.gcn.enhance'],
    url='https://github.com/yyellin/relation_extraction_utils',
    license='GPLv3',
    author='yyellin',
    author_email='yyellin@gmail.com',
    description='Various utilities for processing and analyzing relation extraction related data',
    install_requires=[
        'conllu', 'pytorch_pretrained_bert', 'jsonlines', 'docopt', 'more_itertools', 'stanfordnlp', 'nltk', 'pandas', 'networkx', 'spacy', 'tupa', 'ucca', 'requests', 'stanfordcorenlp', 'ijson'
    ]
)
