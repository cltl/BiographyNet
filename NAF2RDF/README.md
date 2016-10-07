NAF2RDF

BiographyNet crystallization
============================

This package takes Dutch NAF files where the following tools have been applied:

- tokenizer
- Alpino (pos, morphological properties, dependencies and constituents)
- wsd
- named entity recognition
- named entity disambiguation
- SoNar SRL
- FrameNet mapping
- Heideltime
- SimpleTagger identifying professions and family relations

Generic NAF2SEM
---------------

This NAF representation is translated to events modeled according to the Simple Event Model (SEM).
The coversion from NAF2SEM is based on the semantic role layer in NAF:

- predicates are events
- its roles are participants (with labels from propBank and FrameNet)

This step involves one crystallization component: the roles are compared to elements of the entity layer and timex layer.
If the role nearly corresponds to a named entity or time expression, the role's span is replaced by the entity or timex element.

We furthermore link the biography to all lemmas and WordNet identifiers of content words. This information is meant to enhance search (beyond simple keyword)


Target Information
------------------

The simple tagger links expressions referring to a profession to their HISCO code or a wikipedia URI and family relations to a family ontology.

The algorithm applies basic pattern matching rules to link profession mentions to the person who holds the profession as well as to identify the exact family relations.

Biography specific rules are currently being added

Coreference
-----------

We apply a simple algorithm that assumes that pronouns corresponding in number and gender to the subject of the biography, refer to this subject.
We also map entities whose name corresponds to the subject to this person.


Differences with NewsReader NAF2RDF
-----------------------------------

1. Event coreference is ignored in this data. Short biographical descriptions seldom mention the same event twice, this highly overgenerates.
2. This operates primarily on a document level (apart from using metadata). 
