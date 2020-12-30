import pandas as pd
import pandas as pd
import numpy as np
from gensim.utils import simple_preprocess
from gensim.parsing import PorterStemmer
from gensim.parsing.preprocessing import STOPWORDS
from gensim.corpora import Dictionary
from gensim.models import CoherenceModel
from gensim.similarities.docsim import Similarity
from gensim.utils import SaveLoad
import gensim
from nltk.stem import WordNetLemmatizer
import nltk
from dask import delayed
import json
import mysql_config
import pymysql
import datetime
import os
stemmer = PorterStemmer()
def lemmatize_stemming(text):
    return stemmer.stem(WordNetLemmatizer().lemmatize(text, pos='v'))

def connect():
    return pymysql.connect(mysql_config.host,
                       user=mysql_config.name,
                       passwd=mysql_config.password,
                       connect_timeout=5,
                       database='arxiv',
                       port = mysql_config.port)
@delayed
def preprocess(text):
    result=[]
    for token in simple_preprocess(text) :
        if token not in STOPWORDS and len(token) > 2:
            result.append(lemmatize_stemming(token))
    return result


def get_tfidf(articles, tfidf_model = None, corpus_dict = None):
    articles_preprocessed = []
    for art in articles:
        articles_preprocessed.append(preprocess(art))

    # Evaluate dask delayed functions
    for i, art in enumerate(articles_preprocessed):
        articles_preprocessed[i] = art.compute()

    if corpus_dict is None:
        corpus_dict = Dictionary(articles_preprocessed)
        corpus_dict.save('corpus_dict.pckl')

    bow_corpus = [corpus_dict.doc2bow(doc) for doc in articles_preprocessed]
    if tfidf_model is None:
        print('Fitting tfidf model')
        tfidf_model = gensim.models.TfidfModel(bow_corpus, id2word=corpus_dict.id2token,)
        tfidf_model.save('tfidf_model.pckl')
    tfidf_corpus = [tfidf_model[doc] for doc in bow_corpus]
    return tfidf_corpus, corpus_dict

def create_index():
    nltk.download('wordnet')
    conn = connect()
    df = pd.read_sql(""" SELECT id, title, summary FROM articles""", conn)

    articles = (df['title'] + '. ' + df['summary']).tolist()

    tfidf_corpus, corpus_dict = get_tfidf(articles)

    index = Similarity('index', tfidf_corpus, num_features=len(corpus_dict))
    index.save('similarity_index')
    with open('idx_to_arxivid.json','w') as file:
        file.write(json.dumps(df['id'].to_dict()))
    conn.close()


def get_recommendations(user_id, cutoff_days = 20, no_papers=10):
    if not os.path.exists('idx_to_arxivid.json'):
        create_index()
    conn = connect()
    df_bookmarks = pd.read_sql(""" SELECT
                                   articles.id as id,
                                   bookmarks.user_id as user_id,
                                   DATE(updated) as dt,
                                   authors,
                                   title,
                                   summary
                                   FROM articles
                                   INNER JOIN bookmarks
                                   ON articles.id = bookmarks.article_id
                                   WHERE bookmarks.user_id = {}
                                   AND DATE(updated) > DATE_ADD(DATE(NOW()), INTERVAL {:d} day)""".format(user_id, -cutoff_days), conn)
    if len(df_bookmarks):
        with open('idx_to_arxivid.json','r') as file:
            idx_to_arxiv = json.load(file)
        articles = (df_bookmarks['title'] + '. ' + df_bookmarks['summary']).tolist()
        tfidf, _ = get_tfidf(articles, SaveLoad().load('tfidf_model.pckl'), SaveLoad().load('corpus_dict.pckl'))
        index = SaveLoad().load('similarity_index')

        sim = index[tfidf]
        sim = np.argsort(sim, axis=-1)[:,:-1][:,::-1].T.flatten()[:no_papers*no_papers]
        _, unq = np.unique(sim, return_index=True)
        sim = sim[np.sort(unq)]
        rec = [idx_to_arxiv[str(s)] for s in sim[:no_papers]]
        rec = pd.read_sql(""" SELECT * from articles
                     WHERE id in ('{}') """.format("','".join(rec)), conn)
        rec['updated'] = rec['updated'].apply(str)
        conn.close()
        return rec
    else:
        conn.close()
        return None
