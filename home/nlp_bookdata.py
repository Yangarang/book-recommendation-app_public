from django.db import models
from django.db import connection
from collections import namedtuple
from collections import OrderedDict
import threading
import os
import pymysql
import pandas as pd
import re
from ordered_set import OrderedSet
import numpy as np
from numpy import dot
from numpy.linalg import norm
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer,WordNetLemmatizer
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')


# Return all rows from a cursor as a namedtuple
def namedtuplefetchall(cursor):
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

# convert list item to dictionary with book keys
def convert_to_dict(result, cos_sim):
	result = [
		{
            'id': r.book_id,
            'authors': r.book_authors.strip("|").replace("|", ", "),
            'desc': r.book_desc.replace("\r", "\t").replace("\n"," "),
            'edition': r.book_edition,
            'format': r.book_format,
            'isbn': r.book_isbn,
            'pages': r.book_pages,
            'rating': r.book_rating,
            'rating_count': r.book_rating_count,
            'review_count': r.book_review_count,
            'title': r.book_title,
            'genres': r.genres.strip("|").replace("|", ", "),
            'image': r.image_url,
            'cos_score': cos_sim
        }
        for r in result
    ]
	return result


# return ids of all books with similar descriptions
def get_nlpbook_recommendations(**kwargs):
	print("get_nlpbook_recommendations assigned to thread: {}".format(threading.current_thread().name))
	pk = kwargs.get('pk')
	
	# select query of books which only have overlapping genres and sort by rating
	sqlquery = ("""
	SELECT DISTINCT A.* FROM book_data AS A
	INNER JOIN 
		(SELECT * FROM book_data
	    WHERE book_id = '%s') AS B 
	ON (A.genres like CONCAT('%%',B.genres,'%%')
	OR B.genres like CONCAT('%%',A.genres,'%%'))
	AND NOT A.book_id = '%s' AND NOT A.genres = ''
	AND A.book_desc != ''
	ORDER BY A.book_rating
	LIMIT 500
	""" % (pk,pk))
	df_train1 = pd.read_sql(sqlquery, connection)

	# add row of original book id to check
	sqlquery = ("""
	SELECT * FROM book_data WHERE book_id = %s
	""" % (pk))
	df_train2 = pd.read_sql(sqlquery, connection)

	# combining query outputs to one dataframe
	frames = [df_train1, df_train2]
	df_train = pd.concat(frames)

	#Get all unique ids
	bookids = set(df_train['book_id'])
	len(bookids),len(df_train['book_id'])


	#Lambda function with for loop
	df_train['Tokens'] = df_train['book_desc'].apply(lambda x: [tok.lower() for tok in x.split(' ')])

	#Using data structure with lambda
	df_train['unique_words'] = df_train['book_desc'].apply(lambda x: set(tok.lower() for tok in x.split(' ')))

	#stopwords = ['a','and','the','is','have','with','of','it','an','to','their','.','on',',','']
	stop_words = set(stopwords.words('english'))

	def remove_stopwords(text):	    
	    clean_text = OrderedSet()
	    for i in text:
	      i = re.sub('\W','',i)
	      if(i not in stop_words):
	          clean_text.add(i)	            
	    return clean_text

	df_train['Stopwords_Free'] = df_train['unique_words'].apply(lambda x: remove_stopwords(x))

	#Type conversion from ordered set to string type
	df_train['Stopwords_Free'] = df_train['Stopwords_Free'].apply(lambda x: ','.join(x))
	df_modified = df_train.groupby('book_id')['Stopwords_Free'].apply(','.join).reset_index()
	df_modified.sort_values('book_id',ascending=False,inplace=True)

	#ad and set stopwards
	stop_words = set(stopwords.words('english'))
	lemmatizer = WordNetLemmatizer()
	ps = PorterStemmer()

	#clean out stemming and lemmatizer words
	def clean_more(x):  
	    stemming_words = ['ing','ingly','ion','ly','es','s','er','ee','ed','up']
	    words = OrderedSet()
	    for i in x.split(','):
	        w = re.sub('\W','',i)
	        w = lemmatizer.lemmatize(w,pos='v')        
	        for st in stemming_words:
	          if(w.endswith(st)):
	            w = ps.stem(w)
	            break
	        if(w not in stop_words):
	            words.add(w)
	    return ','.join(words)
	df_modified['clean_words'] = df_modified['Stopwords_Free'].apply(lambda x: clean_more(x))


	#Making dictionary to map each word with numeric digit
	corpus = df_modified['clean_words']
	word_vec = {}
	start_marker = 0
	for sentences in corpus:
	    for words in sentences.split(','):
	        if(words not in word_vec):
	            word_vec[words] = start_marker
	            start_marker +=1

	# get vectors of stop words created
	def getVectors(x):
	    vec = []
	    for w in x.split(','):
	        vec.append(word_vec[w])	        
	    return vec
	def getVectorsBinary(x):	    
	    vec = [0]*len(word_vec)
	    for w in x.split(','):
	        vec[word_vec[w]] = 1	        
	    return vec

	# add vectors and binary vectors to output dataframe
	df_modified['vectors'] = df_modified['clean_words'].apply(lambda x: getVectors(x))
	df_modified['binary_vectors'] = df_modified['clean_words'].apply(lambda x: getVectorsBinary(x))

	#See the difference
	len(df_modified['vectors'].iloc[0]),len(df_modified['binary_vectors'].iloc[0])
	sub = df_modified[['book_id','binary_vectors']]
	sub.reset_index(drop=True,inplace=True)
	vectors = sub.loc[:,:]['binary_vectors'].to_list()

	#set up output vectors
	book_id = pk
	scores = []
	vec_a = sub.loc[sub['book_id'] == book_id]['binary_vectors'].to_list()
	max_sim = -float('inf')

	# Return scores that have some similarities
	dict_output = {}
	for j in range(0,len(vectors)):
		vec_b = np.array(vectors[j])

		#Cos score calculation
		cos_sim = dot(vec_a,vec_b)/(norm(vec_a)*norm(vec_b))
		index = j
		if (cos_sim > 0 and sub['book_id'].loc[index] != pk and cos_sim != 1):
			dict_output[str(sub['book_id'].loc[index])] = cos_sim[0]

	dict_output = OrderedDict(sorted(dict_output.items(), key=lambda x: x[1], reverse=True))

	# setup final output
	dict_result_final = []
	with connection.cursor() as cursor:
		for key, value in dict_output.items():
			# run sql command to get book data and convert to dictionary
			cursor.execute("""
	    		SELECT * FROM book_data  
				WHERE book_id = %s
				""",[key])
			list_result = namedtuplefetchall(cursor)
			dict_result = convert_to_dict(list_result, value)

			#add id query result to the final dictionary output
			result = []
			dict_result_final.extend(dict_result)
			for myDict in dict_result_final:
			    if myDict not in result:
			        result.append(myDict)
			dict_result_final = result

	return dict_result_final