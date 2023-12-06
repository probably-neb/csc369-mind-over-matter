::: {#40bc013b .cell .code execution_count="1"}
``` python
#!pip install crosslingual-coreference
#!python -m ipykernel install --user --name spacey_pipeline2
import spacy
import crosslingual_coreference
```

::: {.output .stream .stderr}
    [nltk_data] Downloading package omw-1.4 to /home/myuser/nltk_data...
    [nltk_data]   Package omw-1.4 is already up-to-date!
:::
:::

::: {#9b03ab51 .cell .code execution_count="2"}
``` python
def extract_triplets(text):
    triplets = []
    relation, subject, relation, object_ = '', '', '', ''
    text = text.strip()
    current = 'x'
    for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token
    if subject != '' and relation != '' and object_ != '':
        triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
    return triplets
sent = '<s><triplet> Jennifer Anne Doudna <subj> February 19, 1964 <obj> date of birth <subj> Nobel Prize in Chemistry <obj> award received <triplet> Emmanuelle Charpentier <subj> Nobel Prize in Chemistry <obj> award received</s>'
print(extract_triplets(sent))
```

::: {.output .stream .stdout}
    [{'head': 'Jennifer Anne Doudna', 'type': 'date of birth', 'tail': 'February 19, 1964'}, {'head': 'Jennifer Anne Doudna', 'type': 'award received', 'tail': 'Nobel Prize in Chemistry'}, {'head': 'Emmanuelle Charpentier', 'type': 'award received', 'tail': 'Nobel Prize in Chemistry'}]
:::
:::

::: {#2a23f089 .cell .code execution_count="3"}
``` python
# Add rebel component https://github.com/Babelscape/rebel/blob/main/spacy_component.py
import requests
import re
import hashlib
from spacy import Language
from typing import List

from spacy.tokens import Doc, Span

from transformers import pipeline

def call_wiki_api(item):
  try:
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={item}&language=en&format=json"
    data = requests.get(url).json()
    # Return the first id (Could upgrade this in the future)
    return data['search'][0]['id']
  except:
    return 'id-less'


@Language.factory(
    "rebel",
    requires=["doc.sents"],
    assigns=["doc._.rel"],
    default_config={
        "model_name": "Babelscape/rebel-large",
        "device": -1,
    },
)
class RebelComponent:
    def __init__(
        self,
        nlp,
        name,
        model_name: str,
        device: int,
    ):
        assert model_name is not None, ""
        self.triplet_extractor = pipeline("text2text-generation", model=model_name, tokenizer=model_name, device=device)
        self.entity_mapping = {}
        # Register custom extension on the Doc
        if not Doc.has_extension("rel"):
          Doc.set_extension("rel", default={})

    def get_wiki_id(self, item: str):
        mapping = self.entity_mapping.get(item)
        if mapping:
          return mapping
        else:
          res = call_wiki_api(item)
          self.entity_mapping[item] = res
          return res

    
    def _generate_triplets(self, sent: Span) -> List[dict]:
        output_ids = self.triplet_extractor(sent.text, return_tensors=True, return_text=False)[0]["generated_token_ids"]["output_ids"]
        extracted_text = self.triplet_extractor.tokenizer.batch_decode(output_ids[0])
        extracted_triplets = extract_triplets(extracted_text[0])
        return extracted_triplets

    def set_annotations(self, doc: Doc, triplets: List[dict]):
        for triplet in triplets:
            # Remove self-loops (relationships that start and end at the entity)
            if triplet['head'] == triplet['tail']:
                continue

            # Use regex to search for entities
            head_span = re.search(triplet["head"], doc.text)
            tail_span = re.search(triplet["tail"], doc.text)

            # Skip the relation if both head and tail entities are not present in the text
            # Sometimes the Rebel model hallucinates some entities
            if not head_span or not tail_span:
                continue

            index = hashlib.sha1("".join([triplet['head'], triplet['tail'], triplet['type']]).encode('utf-8')).hexdigest()
            if index not in doc._.rel:
                # Get wiki ids and store results
                doc._.rel[index] = {"relation": triplet["type"], "head_span": {'text': triplet['head'], 'id': self.get_wiki_id(triplet['head'])}, "tail_span": {'text': triplet['tail'], 'id': self.get_wiki_id(triplet['tail'])}}

    def __call__(self, doc: Doc) -> Doc:
        for sent in doc.sents:
            sentence_triplets = self._generate_triplets(sent)
            self.set_annotations(doc, sentence_triplets)
        return doc
```
:::

::: {#e9fd036c .cell .code execution_count="4"}
``` python
DEVICE = -1 # Number of the GPU, -1 if want to use CPU

# Add coreference resolution model
coref = spacy.load('en_core_web_sm', disable=['ner', 'tagger', 'parser', 'attribute_ruler', 'lemmatizer'])
coref.add_pipe(
    "xx_coref", config={"chunk_size": 2500, "chunk_overlap": 2, "device": DEVICE})

# Define rel extraction model

rel_ext = spacy.load('en_core_web_sm', disable=['ner', 'lemmatizer', 'attribute_rules', 'tagger'])
rel_ext.add_pipe("rebel", config={
    'device':DEVICE, # Number of the GPU, -1 if want to use CPU
    'model_name':'Babelscape/rebel-large'} # Model used, will default to 'Babelscape/rebel-large' if not given
    )
```

::: {.output .stream .stderr}
    Some weights of the model checkpoint at nreimers/mMiniLMv2-L12-H384-distilled-from-XLMR-Large were not used when initializing XLMRobertaModel: ['lm_head.dense.bias', 'lm_head.bias', 'lm_head.layer_norm.weight', 'lm_head.layer_norm.bias', 'lm_head.dense.weight']
    - This IS expected if you are initializing XLMRobertaModel from the checkpoint of a model trained on another task or with another architecture (e.g. initializing a BertForSequenceClassification model from a BertForPreTraining model).
    - This IS NOT expected if you are initializing XLMRobertaModel from the checkpoint of a model that you expect to be exactly identical (initializing a BertForSequenceClassification model from a BertForSequenceClassification model).
    Some weights of XLMRobertaModel were not initialized from the model checkpoint at nreimers/mMiniLMv2-L12-H384-distilled-from-XLMR-Large and are newly initialized: ['roberta.pooler.dense.bias', 'roberta.pooler.dense.weight']
    You should probably TRAIN this model on a down-stream task to be able to use it for predictions and inference.
    /home/myuser/spacey_pipeline3/lib/python3.9/site-packages/allennlp/models/archival.py:325: UserWarning: The model models/crosslingual-coreference/minilm/model.tar.gz was trained on a newer version of AllenNLP (v2.9.3), but you're using version 2.10.1.
      warnings.warn(
:::

::: {.output .execute_result execution_count="4"}
    <__main__.RebelComponent at 0x7f4670319220>
:::
:::

::: {#19c174a4 .cell .code execution_count="5"}
``` python

input_text = "Christian Drosten works in Germany. He likes to work for Google."

coref_text = coref(input_text)._.resolved_text

doc = rel_ext(coref_text)

for value, rel_dict in doc._.rel.items():
    print(f"{value}: {rel_dict}")
```

::: {.output .stream .stdout}
    385d9ac30c35635c7e36a1636ded4a091f830cf3: {'relation': 'country of citizenship', 'head_span': {'text': 'Christian Drosten', 'id': 'Q1079331'}, 'tail_span': {'text': 'Germany', 'id': 'Q183'}}
    471a35571b66cc8e1e3415e27f7086505310efc6: {'relation': 'employer', 'head_span': {'text': 'Christian Drosten', 'id': 'Q1079331'}, 'tail_span': {'text': 'Google', 'id': 'Q95'}}
:::
:::

::: {#b09f32ee .cell .code execution_count="6"}
``` python
import pandas as pd
import wikipedia
from neo4j import GraphDatabase

# Define Neo4j connection
host = 'bolt://127.0.0.1:7687'
user = 'neo4j'
password = '12345678'
driver = GraphDatabase.driver(host,auth=(user, password))
```
:::

::: {#dcb0b2dc .cell .code execution_count="7"}
``` python
driver.get_server_info()
```

::: {.output .execute_result execution_count="7"}
    <neo4j.api.ServerInfo at 0x7f46043e46a0>
:::
:::

::: {#4f88283c .cell .code execution_count="8"}
``` python
import_query = """
UNWIND $data AS row
MERGE (h:Entity {id: CASE WHEN NOT row.head_span.id = 'id-less' THEN row.head_span.id ELSE row.head_span.text END})
ON CREATE SET h.text = row.head_span.text
MERGE (t:Entity {id: CASE WHEN NOT row.tail_span.id = 'id-less' THEN row.tail_span.id ELSE row.tail_span.text END})
ON CREATE SET t.text = row.tail_span.text
WITH row, h, t
CALL apoc.merge.relationship(h, toUpper(replace(row.relation,' ', '_')),
  {file_id: row.file_id},
  {},
  t,
  {}
)
YIELD rel
RETURN distinct 'done' AS result;
"""


def run_query(query, params={}):
    with driver.session() as session:
        result = session.run(query, params)
        return pd.DataFrame([r.values() for r in result], columns=result.keys())

import json
def store_content(file):
    #try:
    file_id = file.split("/")[-1].split(".")[0]
    f = open(file)
    doc = json.load(f)
    input_text = doc["text"]
    print(input_text[:100])
    coref_text = coref(input_text)._.resolved_text
    doc = rel_ext(coref_text)
    params = [rel_dict for value, rel_dict in doc._.rel.items()]
    for p in params:
        p['file_id']=file_id
    run_query(import_query, {'data': params})
    #except Exception as e:
    #  print(f"Couldn't parse text for {page} due to {e}")
```
:::

::: {#2e54805f .cell .code execution_count="9"}
``` python
import glob
DIR="domains"
files = glob.glob(DIR + '/*.json')
files
```

::: {.output .execute_result execution_count="9"}
    ['domains/d5.txt.json',
     'domains/d6.txt.json',
     'domains/d1.txt.json',
     'domains/d2.txt.json',
     'domains/d4.txt.json',
     'domains/d3.txt.json']
:::
:::

::: {#f01c91b2 .cell .code execution_count="10"}
``` python
for file in files:
    print(f"Parsing {file}")
    store_content(file)
```

::: {.output .stream .stdout}
    Parsing domains/d5.txt.json
    Familial Attributes

    Genetic and environmental conditions shared in families may contribute to the d
    Parsing domains/d6.txt.json
    Central Schema Attributes

    Many factors determine how pain signals from the periphery are transforme
:::

::: {.output .stream .stderr}
    /home/myuser/spacey_pipeline3/lib/python3.9/site-packages/allennlp/modules/token_embedders/pretrained_transformer_embedder.py:385: UserWarning: __floordiv__ is deprecated, and its behavior will change in a future version of pytorch. It currently rounds toward 0 (like the 'trunc' function NOT 'floor'). This results in incorrect rounding for negative values. To keep the current behavior, use torch.div(a, b, rounding_mode='trunc'), or for actual floor division, use torch.div(a, b, rounding_mode='floor').
      num_effective_segments = (seq_lengths + self._max_length - 1) // self._max_length

    KeyboardInterrupt
:::
:::

::: {#cab1a517 .cell .code execution_count="26" scrolled="true"}
``` python

run_query("""
CALL apoc.periodic.iterate("
  MATCH (e:Entity)
  WHERE e.id STARTS WITH 'Q'
  RETURN e
","
  // Prepare a SparQL query
  WITH 'SELECT * WHERE{ ?item rdfs:label ?name . filter (?item = wd:' + e.id + ') filter (lang(?name) = \\"en\\") ' +
     'OPTIONAL {?item wdt:P31 [rdfs:label ?label] .filter(lang(?label)=\\"en\\")}}' AS sparql, e
  // make a request to Wikidata
  CALL apoc.load.jsonParams(
    'https://query.wikidata.org/sparql?query=' + 
      + apoc.text.urlencode(sparql),
      { Accept: 'application/sparql-results+json'}, null)
  YIELD value
  UNWIND value['results']['bindings'] as row
  SET e.wikipedia_name = row.name.value
  WITH e, row.label.value AS label
  MERGE (c:Class {id:label})
  MERGE (e)-[:INSTANCE_OF]->(c)
  RETURN distinct 'done'", {batchSize:1, retry:1})
""")
     
```

::: {.output .execute_result execution_count="26"}
```{=html}
<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>batches</th>
      <th>total</th>
      <th>timeTaken</th>
      <th>committedOperations</th>
      <th>failedOperations</th>
      <th>failedBatches</th>
      <th>retries</th>
      <th>errorMessages</th>
      <th>batch</th>
      <th>operations</th>
      <th>wasTerminated</th>
      <th>failedParams</th>
      <th>updateStatistics</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>243</td>
      <td>243</td>
      <td>35</td>
      <td>196</td>
      <td>47</td>
      <td>47</td>
      <td>0</td>
      <td>{'Cannot merge the following node because of n...</td>
      <td>{'total': 243, 'committed': 196, 'failed': 47,...</td>
      <td>{'total': 243, 'committed': 196, 'failed': 47,...</td>
      <td>False</td>
      <td>{}</td>
      <td>{'nodesDeleted': 0, 'labelsAdded': 114, 'relat...</td>
    </tr>
  </tbody>
</table>
</div>
```
:::
:::

::: {#d08e57c7 .cell .code}
``` python
```
:::

::: {#723260f2 .cell .code}
``` python
```
:::
