from setuptools import setup

setup(
    name='path_to_re',
    version='0.0.5',
    packages=['path_to_re', 'path_to_re.internal'],
    url='https://github.com/yyellin/relation_extraction_utils',
    license='GPLv3',
    author='yyellin',
    author_email='yyellin@gmail.com',
    description='Various utilities for processing and analyzing relation extraction related data',
    install_requires=[
        'stanfordnlp', 'nltk', 'pandas', 'networkx', 'spacy', 'tupa', 'ucca', 'requests', 'stanfordcorenlp', 'ijson'
    ],
    scripts=[
        'bin/tac_to_csv',
        'bin/parse_ud',
        'bin/parse_ucca',
        'bin/parse_ucca2',
        'bin/append_ner',
        'bin/append_pss',
        'bin/extract_relations_ud',
        'bin/extract_relations_ucca',
        'bin/extract_relations_ud_plus_ucca',
        'bin/filter_relations',

    ]
)
