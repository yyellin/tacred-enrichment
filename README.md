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

## Prerequisites

The modules have been tested on the following environment:

1. Debian 10 (will work on other flavors of Linux) with at least 16G of RAM
2. Python 3.7.3
3. OpenJDK 11.0.8 64bits (for the CoreNLP server)
4. CUDA version 10.0 and 10.1
5. RTX 2070 and RTX 2080

## Environment Setup

It is strongly recommended to following the setup steps without deviation. Make sure to replace `/path/to/virtual/env` and `/target/dir` with your directories of choice.

```bash
python3 -m venv /path/to/virtual/env
```
```bash
source /path/to/virtual/env/bin/activate
```
```bash
pip install --upgrade pip
```
```bash
pip install wheel
```
```bash
pip install git+https://github.com/yyellin/tacred-enrichment.git
```
```bash
wget -O /target/dir/stanford-corenlp-full-2018-10-05.zip  http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
```
```bash
unzip /target/dir/stanford-corenlp-full-2018-10-05.zip -d /target/dir/
```
```bash
mkdir /target/dir/tupa-model ; cd /target/dir/tupa-model; curl -LO https://github.com/huji-nlp/tupa/releases/download/v1.4.0/bert_multilingual_layers_4_layers_pooling_weighted_align_sum.tar.gz; cd -
```
```bash
tar -zxvf /target/dir/tupa-model/bert_multilingual_layers_4_layers_pooling_weighted_align_sum.tar.gz -C /target/dir/tupa-model
```

## Run Enrichment
### Setup

1. Download the TACRED JSON files. For the purpose of these instructions `/target/dir/data` will be the designated directory; replace with your directory of choice.

2. Ensure that you have activated the virtual env by running:
   `source /path/to/virtual/env/bin/activate`

### Step 1 - JSON to "JSON line"

Convert the original JSON  file format into a "JSON line" format, in which there is one valid JSON value per line, each line representing a single sentence.
```bash
python -m tacred_enrichment.extra.json_to_lines_of_json --input /target/dir/data/train.json  --output /target/dir/data/train
```
```bash
python -m tacred_enrichment.extra.json_to_lines_of_json --input /target/dir/data/dev.json  --output /target/dir/data/dev
```
```bash
python -m tacred_enrichment.extra.json_to_lines_of_json --input /target/dir/data/test.json  --output /target/dir/data/test
```

### Step 2 - UCCA Enrichment

Produce a set of "JSON line" files in which each sentence contains the UCCA properties.

```bash
python -m tacred_enrichment.ucca_enrichment /target/dir/tupa-model/bert_multilingual_layers_4_layers_pooling_weighted_align_sum --input /target/dir/data/train --output /target/dir/data/train1
```
```bash
python -m tacred_enrichment.ucca_enrichment /target/dir/tupa-model/bert_multilingual_layers_4_layers_pooling_weighted_align_sum --input /target/dir/data/dev --output /target/dir/data/dev1
```
```bash
python -m tacred_enrichment.ucca_enrichment /target/dir/tupa-model/bert_multilingual_layers_4_layers_pooling_weighted_align_sum --input /target/dir/data/test --output /target/dir/data/test1
```

**Note:** on my setup step 2 takes around 21 hours to complete

### Step 3 - CoreNLP Enrichment

Produce a second set of "JSON line" files in which each sentence contains CoreNLP properties using  the UCCA parser's tokenization
Choose an available port for the CoreNLP server; in the command below I use port 9000. Note that the java command is run with an ampersand, so the StanfordCoreNLPServer is available for the following python commands.

```bash
java -Djava.net.preferIPv4Stack=true  -cp '/target/dir/stanford-corenlp-full-2018-10-05/*' edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000 -threads 2 -maxCharLength 100000 > /dev/null &
```
```bash
python -m tacred_enrichment.corenlp_enrichment localhost 9000 --lines --input /target/dir/data/train1 --output /target/dir/data/train2
```
```bash
python -m tacred_enrichment.corenlp_enrichment localhost 9000 --lines --input /target/dir/data/dev1 --output /target/dir/data/dev2
```
```bash
python -m tacred_enrichment.corenlp_enrichment localhost 9000 --lines --input /target/dir/data/test1 --output /target/dir/data/test2
```

**Note:** on my setup step 3 takes around 3.5 hours to complete

### Step 4 - "JSON line" to JSON

Convert the "JSON line" format back into standard JSON. Backup your original train.json, dev.json and test.json, as the following steps will overwrite them:
```bash
python -m tacred_enrichment.extra.lines_of_json_to_json --input /target/dir/data/train2 --output /target/dir/data/train.json
```
```bash
python -m tacred_enrichment.extra.lines_of_json_to_json --input /target/dir/data/dev2 --output /target/dir/data/dev.json
```
```bash
python -m tacred_enrichment.extra.lines_of_json_to_json --input /target/dir/data/test2 --output /target/dir/data/test.json
```
## License
All work contained in this package is licensed under the Apache License, Version 2.0.

