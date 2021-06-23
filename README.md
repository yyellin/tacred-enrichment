TACRED Enrichment
=================
Why TACRED-enrichment?
----------------------
The TACRED dataset is a leading corpus for Relation Extraction model development, analysis and benchmarking  (see, for example,  ["Relation extraction on TACRED"](https://paperswithcode.com/sota/relation-extraction-on-tacred#:~:text=TACRED%20is%20a%20large%2Dscale,Population%20(TAC%20KBP)%20challenges) ).

The TACRED dataset, available for download  from the [LDC TACRED webpage](https://catalog.ldc.upenn.edu/LDC2018T24) in json format, contains spans for the *subject* and *object* identified in each sentence, and one of the 42 entity relation attributes, or a *no\_relation* classification if no relation exists.  Additionally, TACRED contains contains POS tags, named entities and UD parses by the Standford CORENLP parser. 
The aim of this project is to support enrichment of the TACRED dataset with additional semantic and syntactic attributes, where such additional attributes are required by downstream models. 

## Enrichment Steps
Two enrichment steps are implemented:

### UCCA 

The [Universal Conceptual Cognitive Annotation framework](https://universalconceptualcognitiveannotation.github.io/) is a multi-layered system for semantic representation that seeks to capture the semantic, rather than syntactic patterns, expressed through linguistic utterances. 

The `ucca_enrichment` module accepts TACRED json as input, producing json output with all original properties, and a set of new properties relevant for UCCA.

### CoreNLP

[TUPA](https://github.com/danielhers/tupa), the standard UCCA parser, uses the the SpaCy NLP pipeline for basic NLP tasks, including tokenization. SpaCy's default tokenization results vary considerably from TACRED's given tokenization. Additionally, the TACRED dataset contains some obvious tokenization errors; for example there are over 130 entries in which two sentences have been merged into one, by erroneously fusing the last token of the first sentence, it's period punctuation mark, and the first one of the next sentence into a single token. 

To address these tokenization concerns, the second enrichment step re-parses all TACRED sentences with the Standford CORENLP parser, configuring it to adhere to the given tokenization produced by the TUPA parser. This results in a tokenization-aligned `corenlp_pos`, `corenlp_head`,  and `corenlp_ner` attribute set.

## Setup

|      | Step                                                         | Command                                                      |
| ---- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 1    | Create a virtualenv                                          | `python3 -m venv /path/to/virtual/env`                       |
| 2    | Update to latest version of pip                              | `pip install --upgrade pip`                                  |
| 3    | Install wheel                                                | `pip install wheel`                                          |
| 4    | Install the TACRED-enrichment module                         | `pip install git+https://github.com/yyellin/tacred-enrichment.git` |
| 5    | Download `stanford-corenlp-full-2018-10-05.zip` to your working directory (choose `/target/dir` appropriately) | `wget -O /target/dir/stanford-corenlp-full-2018-10-05.zip  http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip` |
| 6    | Unzip `stanford-corenlp-full-2018-10-05.zip`                 | `unzip /target/dir/stanford-corenlp-full-2018-10-05.zip -d /target/dir/` |
| 7    | Download pre-trained BERT models for TUPA parser to your working directory  (using the same `/target/dir`) | `mkdir /target/dir/tupa-model ; cd /target/dir/tupa-model; curl -LO https://github.com/huji-nlp/tupa/releases/download/v1.4.0/bert_multilingual_layers_4_layers_pooling_weighted_align_sum.tar.gz; cd -` |
| 8    | Un-tar `bert_multilingual_layers_4_layers_pooling_weighted_align_sum.tar.gz` | `tar -zxvf /target/dir/tupa-model/bert_multilingual_layers_4_layers_pooling_weighted_align_sum.tar.gz -C /target/dir/tupa-model` |

Run
-------

