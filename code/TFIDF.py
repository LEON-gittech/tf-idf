# import pandas as pd
# import numpy as np
# import re
# import nltk
# from collections import Counter
# import scipy.sparse as sp
# from numpy.linalg import norm

# class TFIDF(object):

#     def __init__(self, corpus):        
#         self.corpus = corpus
#         self.norm_corpus  = None    

#     def __normalize_corpus(self, d):
#         stop_words = nltk.corpus.stopwords.words('english')
#         d = re.sub(r'[^a-zA-Z0-9\s]', '', d, re.I|re.A)
#         d = d.lower().strip()
#         tks = nltk.word_tokenize(d)
#         f_tks = [t for t in tks if t not in stop_words]
#         return ' '.join(f_tks)

#     def preprocessing_text(self):
#         n_c = np.vectorize(self.__normalize_corpus)
#         self.norm_corpus = n_c(self.corpus)

#     def tf(self):
#         words_array = [doc.split() for doc in self.norm_corpus]
#         words = list(set([word for words in words_array for word in words]))
#         features_dict = {w:0 for w in words}
#         tf = []
#         for doc in self.norm_corpus:
#             bowf_doc = Counter(doc.split())
#             all_f = Counter(features_dict)
#             bowf_doc.update(all_f)
#             tf.append(bowf_doc)
#         return pd.DataFrame(tf)

#     def df(self, tf):
#         features_names = list(tf.columns)
#         df = np.diff(sp.csc_matrix(tf, copy=True).indptr)
#         df = 1 + df
#         return df
        
#     def idf(self, df):
#         N = 1 + len(self.norm_corpus)
#         idf = (1.0 + np.log(float(N) / df)) 
#         idf_d = sp.spdiags(idf, diags= 0, m=len(df), n= len(df)).todense()      
#         return idf, idf_d

#     def tfidf(self, tf, idf):        
#         tf = np.array(tf, dtype='float64')
#         tfidf = tf * idf
#         norms = norm(tfidf , axis=1)
#         return (tfidf / norms[:,None])

import pandas as pd
import numpy as np
import re
import nltk
from collections import Counter
import scipy.sparse as sp
from numpy.linalg import norm
from concurrent.futures import ProcessPoolExecutor, as_completed

class TFIDF(object):

    def __init__(self, corpus, num_workers=1):        
        self.corpus = corpus
        self.norm_corpus  = None  
        self.num_workers = num_workers

    def normalize_corpus(self, d):
        stop_words = nltk.corpus.stopwords.words('english')
        d = re.sub(r'[^a-zA-Z0-9\s]', '', d, re.I|re.A)
        d = d.lower().strip()
        tks = nltk.word_tokenize(d)
        f_tks = [t for t in tks if t not in stop_words]
        return ' '.join(f_tks)

    def preprocessing_text(self):
        n_c = np.vectorize(self.normalize_corpus)
        self.norm_corpus = n_c(self.corpus)

    def compute_tf(self, doc):
        words_array = doc.split()
        features_dict = {w:0 for w in words_array}
        tf_doc = Counter(words_array)
        all_f = Counter(features_dict)
        tf_doc.update(all_f)
        return tf_doc

    def tf(self):
        with ProcessPoolExecutor(self.num_workers) as executor:
            results = [executor.submit(self.compute_tf, doc) for doc in self.norm_corpus]
        tf = pd.DataFrame([r.result() for r in as_completed(results)])
        columns = sorted(tf.columns, key=lambda x: str(x))
        tf = tf[columns]
        return tf

    def compute_df(self, tf):
        df = np.diff(sp.csc_matrix(tf, copy=True).indptr)
        df = 1 + df
        return df
        
    def df(self, tf):
        with ProcessPoolExecutor(self.num_workers) as executor:
            results = [executor.submit(self.compute_df, tf)]
        df = results[0].result()
        return df

    def compute_idf(self, df):
        N = 1 + len(self.norm_corpus)
        idf = (1.0 + np.log(float(N) / df)) 
        idf_d = sp.spdiags(idf, diags= 0, m=len(df), n= len(df)).todense()      
        return idf, idf_d

    def idf(self, df):
        with ProcessPoolExecutor(self.num_workers) as executor:
            results = [executor.submit(self.compute_idf, df)]
        idf, idf_d = results[0].result()
        return idf, idf_d

    def compute_tfidf(self, tf, idf):        
        tf = np.array(tf, dtype='float64')
        tfidf = tf * idf
        norms = norm(tfidf , axis=1)
        return (tfidf / norms[:,None])

    def tfidf(self, tf, idf):     
        with ProcessPoolExecutor(self.num_workers) as executor:
            results = [executor.submit(self.compute_tfidf, tf, idf)]
        tfidf = results[0].result()
        return tfidf