from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.sql.expression import join
from icog_util import remove_stop_words
import pandas as pd
import logging as log
import sys
import os
from db_util import engine, Item, ItemVector
from timeit import default_timer as timer
from keyphrase_extractor import KeyphraseExtraction
from icog_util import remove_stop_words
from sentence_transformers import SentenceTransformer, util

log.basicConfig(stream=sys.stdout, format='%(asctime)s - %(message)s',
                level=log.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')


sentance_transformer = SentenceTransformer(
    'paraphrase-MiniLM-L6-v2', device='cpu')
keyphrase_extractor = KeyphraseExtraction()


def add_context_to_wikidata_label(label, description):
    """This method adds context to short wikidata item label 
    by adding keyphrase from the description to the text. 
    This method is used by the embedd wikidata label.

    Args:
        label (str): label of the wikidata entity
        description (str): description of the wikidata entity
    """
    results = []
    if (len(label.split(' ')) <= 2):
        # logging.info(f"Adding context to {label} with description {description}")
        keyphrases = keyphrase_extractor(description)

        "Adding keyphrase to short label to add context to the label."
        if (len(keyphrases) > 0):
            for keyphrase in keyphrases:
                """
                If the keyphrase score is higher than 0.8, we add the keyphrase to the label.
                """
                if (keyphrase.get('score') > 0.8):
                    results.append(label + ' ' + keyphrase.get('word'))

        """
        If there is no keyphrase in the description, 
        we add remove stop words from the description and add the first 4 words to the label.
        """
        if (len(results) == 0):
            results.append(
                label + ' ' + remove_stop_words(description, return_format='list')[:3])

    # In case label have two words, also add it to the results.
    # In this case, we keep the original plus the context around it.
    if (len(label.split(' ')) == 2):
        results.append(label)
    else:
        results.append(label)

    return results


def embedd_wikidata_label(label, description) -> dict:
    """This method generate embeeding from wikidata label and description of the entity."""

    results = []
    labels = add_context_to_wikidata_label(label, description)
    for l in labels:
        vector = sentance_transformer.encode(
            l, show_progress_bar=False, batch_size=10)
        results.append({"text": l, "embedding": vector})

    return results


class GenerateVectors:

    def generateItemVector(self, item: Item) -> list[ItemVector]:

        results = []
        for embedded_item in embedd_wikidata_label(item.label, item.description):
            iv = ItemVector()
            iv.wikidata_id = item.id
            iv.text = embedded_item['text']
            iv.text_vec = embedded_item['embedding']
            results.append(iv)
        return results

    def getProgress(self) -> float:
        """Calculate what percentage of the items were processed and added embedding"""
        subquery = select(ItemVector.wikidata_id)
        done_stmt = select(func.count()).select_from(
            Item).where(Item.id.in_(subquery))

        j = join(Item, ItemVector, Item.id == ItemVector.wikidata_id)
        done_stmt = select(func.count()).select_from(j)

        total_stmt = select(func.count()).select_from(Item).where(
            Item.description != None, Item.views > 454)

        with Session(engine) as session:
            number_done = session.scalar(done_stmt)
            total = session.scalar(total_stmt)

        return round((number_done/total), 4)

    def GenerateEmbeddingForItems(self, window=10000):
        """ 
            Generate ItemVector objects from Items and insert the ItemVectors into DB. 
            This is recursive funtion that will generate vector until all items are processed.
            The window is the number of items that will be processed at a time.
            This function will return False if no more items without embedding were found.
        """

        """Get all items that are not in the ItemVector table that have a decription and views is above the average (454)"""
        left_join = join(Item, ItemVector, Item.id ==
                         ItemVector.wikidata_id, isouter=True)
        stmt = select(Item).select_from(left_join).where(
            ItemVector.wikidata_id == None,
            Item.description != None,
            Item.views > 454).limit(window)

        # Get the next window of wikidata concepts
        with Session(engine) as session:
            start_time = timer()
            items = session.scalars(stmt).all()
            end_time = timer()
            log.info(
                f"Time elapsed  to get items without embedding: {round((end_time - start_time), 2)} seconds. {len(items)} items")

            if (len(items) == 0):
                log.info(f"No more items without embedding")
                return False

            start_time = timer()

            itemsVencors = []
            for item in items:
                for subitem in self.generateItemVector(item):
                    itemsVencors.append(subitem)

            end_time = timer()
            log.info(
                f"Time elapsed to generate item vectors: {round((end_time - start_time), 2)} seconds")

            start_time = timer()
            session.add_all(itemsVencors)
            session.commit()
            end_time = timer()
            log.info(
                f"Time elapsed to commited item vectors list into database: {round((end_time - start_time), 2)} seconds")
            percDone = self.getProgress()
            log.info(
                f"Percent of items with embedding: {percDone}")

            return True


if __name__ == '__main__':

    generate_vectors = GenerateVectors()

    # Generate vectors
    items = generate_vectors.GenerateEmbeddingForItems(window=10000)
    while items:
        items = generate_vectors.GenerateEmbeddingForItems(window=10000)
