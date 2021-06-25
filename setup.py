from setuptools import setup

setup(
    name='tacred_enrichment',
    version='1.0.0',
    packages=['tacred_enrichment', 'tacred_enrichment.extra', 'tacred_enrichment.internal'],
    url='https://github.com/yyellin/tacred-enrichment',
    license='Apache 2.0',
    author='Jonathan Yellin',
    author_email='jonathan.yellin@mail.huji.ac.il',
    description='A set of modules for supplementing the TACRED dataset with additional attributes, to be used by downstream RE neural networks',
    install_requires=[
        'conllu', 'pytorch_pretrained_bert', 'jsonlines', 'docopt', 'more_itertools', 'stanfordnlp', 'nltk', 'pandas', 'networkx', 'spacy', 'tupa==1.4.2', 'ucca==1.2.3', 'requests', 'stanfordcorenlp', 'ijson'
    ]
)
