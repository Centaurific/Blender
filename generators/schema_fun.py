import os
os.chdir(os.getenv('HOME') + '/Documents/Blender')
import wikipedia
import spacy
from nltk.corpus import wordnet as wn
from utils import text_fun
#from utils.wiki_sim import wiki_query
from gensim.models import KeyedVectors, Word2Vec


nlp = text_fun.nlp 

def get_ref_concepts(seed_term, method='quick'):
    if method == 'quick':
        seed_term = seed_term.split()
        seed_term = seed_term[len(seed_term) - 1]
        mod = KeyedVectors.load_word2vec_format('aux/deps.words.vector', 
            binary=False)
        mod.init_sims(replace=True)
        out = mod.most_similar(seed_term) 
        out = [item[0] for item in out]
        return out
    #elif method == 'LSI':
    #    out = wiki_query.similar(seed_term)
    #    out = [el for el in out if el.lower() != seed_term]
    #    return out
    elif method == 'wordnet':
        out = []
        for term in seed_term.split():
            hypernyms = wn.synsets(term)[0].hypernyms()
            for nym in hypernyms:
                hyponyms = nym.hyponyms()
                for nym in hyponyms:
                    name = nym.name()
                    word = name[0:name.find('.')]
                    out.append(word)
        return out
    else:
        out3 = []
        for term in seed_term.split():
            hypernyms = wn.synsets(term)[0].hypernyms()
            for nym in hypernyms:
                hyponyms = nym.hyponyms()
                for nym in hyponyms:
                    name = nym.name()
                    word = name[0:name.find('.')]
                    out3.append(word)
        #out2 = wiki_query.similar(seed_term)
        #out2 = [el for el in out2 if el.lower() != seed_term]
        seed_term = seed_term.split()
        seed_term = seed_term[len(seed_term) - 1]
        mod = Word2Vec.load_word2vec_format('aux/deps.words.vector', 
            binary=False)
        mod.init_sims(replace=True)
        out1 = mod.most_similar(seed_term) 
        out1 = [item[0] for item in out1]
        #out1.extend(out2)
        out1.extend(out3)
        return out1

def limit_filter(tuple_index, new_ideas, max_num=3, score_index=3):
    items = set([el[tuple_index] for el in new_ideas])
    out = []
    for item in items:
        sub_ideas = [el for el in new_ideas if el[tuple_index] == item]
        if sub_ideas:
            if max_num == 1:
                out.extend(min(sub_ideas, key=lambda x: x[score_index]))
            else:
                ranked_sub = sorted(sub_ideas, key=lambda x: x[score_index])
                out.extend(ranked_sub[0:(max_num - 1)])
    return out

def get_header_tags(seed_term):
    header = wikipedia.summary(seed_term)
    header = header[0:header.find('\n')]
    header = nlp(header)
    header_tags = []
    for item in header:
        if not item.is_stop:
            if not item.pos_ == 'PUNCT':
                header_tags.append((item, item.tag_))
    return header_tags

def build_model(seed_term, ref_concepts, targets, article):
    sentences = text_fun.w2v_sent_prep(article)
    for ref_concept in ref_concepts:
        try:
            ref_article = wikipedia.page(ref_concept).content
            ref_sentences = text_fun.w2v_sent_prep(ref_article)
            sentences.extend(ref_sentences)
            print('Got article for %s' % ref_concept) 
        except:
            continue
    for target in targets:
        try:
            if seed_term != target:
                target_article = wikipedia.page(target).content
                print('Got a target article for %s' % target)
                target_sentences = text_fun.w2v_sent_prep(target_article)
                sentences.extend(target_sentences)
        except:
            continue
    flat_sentences = [word for sublist in sentences for word in sublist]
    model = Word2Vec(sentences, sg=1, negative=10)
    return model

def schema_framer(seed_term, targets, ref_concepts, model, 
    ksEvaluator, ok_tags, article):
    new_ideas = []
    seed_term = seed_term.split()
    seed_term = seed_term[len(seed_term) - 1]
    article_tokens = text_fun.prune(article)
    for target in targets:
        print('Target: %s' % target)
        for ref_concept in ref_concepts:
            candidates = model.most_similar(positive=[target, 
                ref_concept], negative=[seed_term])
            candidates = [el[0] for el in candidates]
            for candidate in candidates:
                cand_pos = nlp(candidate)[0].tag_
                if cand_pos in ok_tags:
                    temp = list(article_tokens)
                    temp.append(candidate)
                    score = ksEvaluator(temp)
                    print(score)
                    if cand_pos == 'JJ':
                        next_idea = 'Try making %s more %s.' % \
                        (seed_term, candidate)
                        out = (next_idea, target, ref_concept, score, 
                               candidate)
                        new_ideas.append(out)
                    elif cand_pos == 'NN':
                        next_idea = 'Try using the %s from a %s to make a new %s.' % \
                            (candidate, ref_concept, seed_term)
                        out = (next_idea, target, ref_concept, score, candidate)
                        new_ideas.append(out)
    return new_ideas


