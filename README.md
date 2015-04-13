BiographyNet
============

NLP tools and data used in BiographyNet

Current status:
--------------

The full corpus can be obtained by e-mailing antske.fokkens@vu.nl
Scripts are currently being cleaned added. Please e-mail antske.fokkens@vu.nl if you need scripts that are not available yet.

Development Corpus:
------------------

Consists of a small set of files (at least 10) from different sources.

NB1: elias and nbwv have metadata but no text
NB2: bwsa_archives glasius schilderkunst and schouburg are currently empty. Metadata in these sources only provide a name and texts are not included in the XML file.

Each file contains the XML file and some have a folder "metadata_values" that provides tags and their value as extracted from the metadata.

CleanedDevelopmentCorpus:
-------------------------

Version of the development corpus where HTML mark up is removed from text and characters are converted to utf-8.
Output of first version of clean-up scripts (available in DataPreparation)

DataPreparation:
---------------

Provides scripts needed to prepare the experiment. It currently contains:


extract_from_xml.py: a basic script that provides functions to retrieve specific information from the XML schema used in BiographyNet data

clean_html_texts.py: takes a directory as input (and optionally an output directory). It creates a version of biographical text without HTML markup from all .xml files in the input directory in the output directory. If no output directory is given, a directory is created that has the same name as the input directory with '-html-cleaned' as a suffix (if the input directory already ends in '-cleaned' it will insert '-html' before '-cleaned' in the output directory name).

convert_characters_to_utf8.py: takes a directory name as input and for all .xml files and creates a copy in an output directory that is encoded in utf-8. Also attempts to replace HTML encodings, but this does not work 100% at the moment. A name for the output directory can be given, else a directory is created that has the name of the input directory with suffix '-cleaned'. If the input directory ends with '-html-cleaned' the name of the output directory will be the same with '-html' removed.

The recommended order to run these scripts is:

1. clean_html_texts.py
2. convert_characters_to_utf8.py

Since the html parser does not like certain utf-8 encoded characters...



  





Preliminary outcome of text mining for different categories of information:
--------------------------------------------------------------------------

Total information 71 individuals

Finding the correct instance:
----------------------------

Birthdate (available for 71): 

Correct: 21 Incorrect: 2

Occupation (available for 70):

Correct: 14 Incorrect: 6 Both correct and incorrect information: 2

Education (available for 71):

Correct: 2 Incorrect: 0

Finding the sentence that contains the information:
--------------------------------------------------

Birthdate: 35

Occupation: 21

Education: 2

Mother: 2

Father: 9




