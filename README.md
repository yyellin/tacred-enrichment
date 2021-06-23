TACRED Enrichment
=================


Why tacred-enrichment?
----------------------

The TACRED dataset is the goto corpus for Relation Extraction model comparison and benchmarking (https://paperswithcode.com/sota/relation-extraction-on-tacred#:~:text=TACRED%20is%20a%20large%2Dscale,Population%20(TAC%20KBP)%20challenges).
TACRED.

TACRED was designed by \citet{zhang2017position} to address the dearth of annotated data required for supervised learning for RE. It is based on examples from the corpus used in the yearly TAC Knowledge Base Population (TAC KBP) challenges, conducted from 2009 to 2015 \citep{mcnamee2009overview}. In each annual challenge, 100 entities, people, and organizations, were provided to competing systems for them to identify relations between those given entities (referred to as \textit{subjects}), and other \textit{objects} mentioned in the text. The TAC KBP relation extraction task was formulated in terms of slot filling: a person entity is assigned 26 attribute types while an organization is assigned 16 --- the challenge posed to competing systems being the extraction of the values of these attributes based on the given corpus (or in other words, the object and relation are given; the challenge is to find the subject). TACRED leverages the results of these challenges to form a set of 106,264 example sentences, each one containing an object and a subject. 



Requirements
------------


License
-------
