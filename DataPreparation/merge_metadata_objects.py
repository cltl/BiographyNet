#!usr/bin/python
# -*- coding: utf-8 -*
import metadata




def update_metadata(singleMeta, completeMeta):
    completeMeta.name.append(singleMeta.name)
    completeMeta.birth.append(singleMeta.birth)
    completeMeta.death.append(singleMeta.death)
    completeMeta.father.append(singleMeta.father)
    completeMeta.mother.append(singleMeta.mother)
    completeMeta.education.append(singleMeta.education)
    completeMeta.occupation.append(singleMeta.occupation)
    completeMeta.gender.append(singleMeta.gender)
    completeMeta.religion.append(singleMeta.religion)
    completeMeta.otherEvents.append(singleMeta.otherEvents)
    completeMeta.otherStates.append(singleMeta.otherStates)
    completeMeta.text.append(singleMeta.text)

    return completeMeta


def merge_metadata_objects(myMetadatalist):

    #get standard info from 
    idNr = get_idnr(myMetadatalist[0])
    mergedMetadata = metadata.MetadataComplete(idNr)

    for singleMeta in myMetadatalist:
        update_metadata(singleMeta, completeMeta)