# This script needs a gensim corpus, an associated gensim dictionary, and
# an associated gensim lsi (or lda) model to work. In what follows,
# 'Aux/wiki_en_tfidf.mm' is a gensim corpus saved on disk in market matrix format,
# 'wiki_en_wordids.txt' is the associated dictionary,
# and 'wiki_en_lsi' is the the associated lsi model.

import os
import gensim
import sys



def find_similar(doc):
    os.chdir(os.getenv('HOME') + '/Documents/Blender')
    AuxPath = os.getenv('HOME') + '/Documents/Blender/Aux'

    # Load a previously created corpus in tfidf format
    wikiCorpus = gensim.corpora.MmCorpus('Aux/wiki_en_tfidf.mm')

    # Loads a previously created dictionary from 'wiki_en_wordids.txt'.
    # A dictionary object can map between words and their ids.
    id2word = gensim.corpora.Dictionary.load_from_text('wiki_en_wordids.txt')

    # Loads a pre-computed lsi model named 'wiki_en_lsi'.  
    # Type str(lsi) for basic info.
    lsi = gensim.models.LsiModel.load('wiki_en_lsi')

    # Transform wikiCorpus from tfidf space to lsi space using lsi object
    lsiCorpus = lsi[wikiCorpus]

    # Split doc, change to BOW (bag of words) and translate to lsi space 
    lsiString = lsi[id2word.doc2bow(doc.split())]

    #------------------------------------------------------------------------------
    # Comment this block out if you already have lsiWikiIndex.index,
    # since otherwise it will take some major time
    #------------------------------------------------------------------------------
    #
    # Takes a corpus (lsiCorpus in this case), and creates a document index.
    # Basically represents the documents in lsi space. The documents are stored
    # to disk as a series of 'shards'. The shards have the prefix lsiWikiIndex
    # and are stored in './Aux'.  
    #index =
    #    gensim.similarities.docsim.Similarity('./Aux/indexShards/lsiWikiIndex',
    #                                         lsiCorpus,
    #                                         num_features = lsi.num_topics,
    #                                         num_best = 1
    #                                         )
    # Save the index 
    #index.save('./Aux/indexShards/lsiWikiIndex.index')
    #
    #------------------------------------------------------------------------------

    # Load the index
    index = gensim.similarities.docsim.Similarity.load(
        './Aux/indexShards/lsiWikiIndex.index'
        )

    similar = index[lsiString]

    # docNumber is the index of the document from the corpus which is closest
    # to the query in lsi space.  
    docNumber = similar[0][0]
    return docNumber
