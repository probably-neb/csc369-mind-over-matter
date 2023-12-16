#!/usr/bin/env python
import pandas as pd
import spacy, ray, json, requests, re, hashlib

def call_wiki_api(item):
  try:
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={item}&language=en&format=json"
    data = requests.get(url).json()
    # Return the first id (Could upgrade this in the future)
    return data['search'][0]['id']
  except:
    return 'id-less'

DEVICE = -1 # Number of the GPU, -1 if want to use CPU

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

def run_query(driver, query, params={}):
    if not driver:
        return None
    with driver.session() as session:
        result = session.run(query, params)
        return pd.DataFrame([r.values() for r in result], columns=result.keys())

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



@ray.remote
def store_content(file):

    from spacy import Language
    from typing import List

    from spacy.tokens import Doc, Span
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
            from transformers import pipeline
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
            output_ids = self.triplet_extractor(sent.text, return_tensors=True, return_text=False)
            output_ids = output_ids[0]["generated_token_ids"]
            extracted_text = self.triplet_extractor.tokenizer.batch_decode([output_ids])[0]
            extracted_triplets = extract_triplets(extracted_text)
            print(f'{extracted_triplets=}')
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

    # Define rel extraction model
    rel_ext = spacy.load('en_core_web_sm', disable=['ner', 'lemmatizer', 'attribute_rules', 'tagger'])
    rel_ext.add_pipe("rebel", config={
    'device':DEVICE, # Number of the GPU, -1 if want to use CPU
    'model_name':'Babelscape/rebel-large'} # Model used, will default to 'Babelscape/rebel-large' if not given
    )

    file_id = file.split("/")[-1].split(".")[0]
    f = open(file)
    doc = json.load(f)
    input_text = doc["text"]
    print(f'{input_text[:100]=}')
    doc = rel_ext(input_text)
    params = [rel_dict for value, rel_dict in doc._.rel.items()]
    for p in params:
        p['file_id']=file_id
    print(f'{params=}')
    if driver:
        run_query(driver, import_query, {'data': params})


import argparse

parser = argparse.ArgumentParser(description='Neo4j Pipeline')
parser.add_argument('--files', nargs='+', help='List of files to parse', required=True)
parser.add_argument('--host', help='Neo4j host', default='bolt://neo4j:7687')
parser.add_argument('--user', help='Neo4j user', default='neo4j')
parser.add_argument('--password', help='Neo4j password', default='12345678')

if __name__ == "__main__":
    args = parser.parse_args()
    files = args.files
    host, user, password = args.host, args.user, args.password

    ray.init()

    driver = None

    results = []
    for file in files:
        print(f"parsing {file}")
        result = ray.get(store_content.remote(file))
        results.append(result)

    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(host,auth=(user, password))
    except Exception:
        pass
    print(driver.get_server_info())
    if driver:
        for params in results:
            run_query(driver, import_query, {'data': params})


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
