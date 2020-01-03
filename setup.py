from setuptools import setup

setup(
    name='path_to_re',
    version='0.0.5',
    packages=['path_to_re', 'path_to_re.e2e', 'path_to_re.internal'],
    url='https://github.com/yyellin/relation_extraction_utils',
    license='GPLv3',
    author='yyellin',
    author_email='yyellin@gmail.com',
    description='Various utilities for processing and analyzing relation extraction related data',
    install_requires=[
        'stanfordnlp', 'nltk', 'pandas', 'networkx', 'spacy', 'tupa', 'ucca', 'requests', 'stanfordcorenlp', 'ijson'
    ]
)
