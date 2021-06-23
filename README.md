TACRED Enrichment
=================
Why TACRED-enrichment?
----------------------
The TACRED dataset is a leading corpus for Relation Extraction model development, anaylsis and benchmarking  (see, for example,  ["Relation extraction on TACRED"](https://paperswithcode.com/sota/relation-extraction-on-tacred#:~:text=TACRED%20is%20a%20large%2Dscale,Population%20(TAC%20KBP)%20challenges) ).

TACRED was designed by Yuhao Zhang, Victor Zhong , Danqi Chen, Gabor Angeli and Christopher D. Manning to address the dearth of annotated data required for supervised learning for RE. It is based on examples from the corpus used in the yearly TAC Knowledge Base Population (TAC KBP) challenges, conducted from 2009 to 2015. In each annual challenge, 100 entities, people, and organizations, were provided to competing systems for them to identify relations between those given entities (referred to as *subjects*), and other *objects* mentioned in the text. The TAC KBP relation extraction task was formulated in terms of slot filling: a person entity is assigned 26 attribute types while an organization is assigned 16 --- the challenge posed to competing systems being the extraction of the values of these attributes based on the given corpus. TACRED leverages the results of these challenges to form a set of 106,264 example sentences, each one containing an object and a subject. 

The TACRED dataset, available for download  from the [LDC TACRED webpage](https://catalog.ldc.upenn.edu/LDC2018T24) in json format, contains spans for the *subject* and *object* identified in each sentence, and one of the 42 entity relation attributes, or a *no\_relation* classification if no relation exists.  Additionally, TACRED contains contains POS tags, named entities and UD parses by the Standford CORENLP parser. 
The aim of this project is to support enrichment of the TACRED dataset with additional semantic and syntactic attributes, where such additional attributes are required by downstream models. 

## Enrichment Steps
Two enrichment steps are implemented:

### UCCA 

The [Universal Conceptual Cognitive Annotation framework](https://universalconceptualcognitiveannotation.github.io/) is a multi-layered system for semantic representation that seeks to capture the semantic, rather than syntactic patterns, expressed through linguistic utterances. The UCCA scheme maps sentences to DAGs that embody these semantic structures. In contrast to graphs formed by dependency grammars, whose nodes all represent lexical entities, a UCCA graph contains both nodes that represent word terminals, which are leaves in the DAG, and non-leaf nodes that represent entities according to some semantic consideration. The foundational layer of UCCA covers the semantics of predicate-argument structure evoked by predicates of all grammatical categories (verbal, nominal, adjectival and others). The layer's primary construct is a *scene*, which captures a temporally persistent state or an evolving event. A *scene* contains one or more *participants*, and may also contain secondary scenes, known as *adverbials*. *Scene*, *participant* and *adverbial* manifest as units in the DAG. 

The `ucca_enrichment` module accepts TACRED json as input, producing json output with all original properties, and a set of new properties relevant for UCCA.

### CoreNLP

[TUPA](https://github.com/danielhers/tupa), the standard UCCA parser, uses the the SpaCy NLP pipeline for basic NLP tasks, including tokenization. SpaCy's default tokenization results vary considerably from TACRED's given tokenization. Indeed, in 30% of train sentences, 28% of dev sentences, and 25% of test sentences tokenization is different. For example, differences arise in the case of intra-word-hyphens (discussion on this tokenization divergence on [Stack Overflow](https://stackoverflow.com/questions/52293874/why-does-spacy-not-preserve-intra-word-hyphens-during-tokenization-like-stanford)). Additionally, the TACRED dataset contains some obvious tokenization errors; for example there are over 130 entries in which two sentences have been merged into one, by erroneously fusing the last token of the first sentence, it's period punctuation mark, and the first one of the next sentence into a single token. 

To address these tokenization concerns, the second enrichment step re-parses all TACRED sentences with the Standford CORENLP parser, configuring it to adhere to the given tokenization produced by the TUPA parser. This is achieved by reconstructing each sentence by conjoining all TUPA generated tokens with a whitespace in between them, and then setting CORE NLP's  `tokenize.whitespace` flag to True. This results in a tokenization-aligned `corenlp_pos`, `corenlp_head`,  and `corenlp_ner` attribute set.

## Setup

- [ ] Create a `virtualenv` by running: `python3 -m venv /path/to/virtual/env`
- [ ] Critical to update pip to the latest version by running: `pip install --upgrade pip`
- [ ] Install wheel by running: `pip install wheel`
- [ ] Install the TACRED-enrichment module by running: `pip install git+https://github.com/yyellin/tacred-enrichment.git`
- [ ] Download the stanford-corenlp-full-2018-10-05 by running 


License
-------
