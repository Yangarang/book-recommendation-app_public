from django.db import models
from django.db import connection
from collections import namedtuple
import threading
import os
#from django.contrib.auth.models import user


# Models: https://docs.djangoproject.com/en/3.0/ref/models/fields/
# book class is table in database and fields
# class Book(models.Model):
# 	book_id = models.CharField(max_length=100, primary_key =True)
# 	book_authors = models.CharField(max_length=1000)
# 	book_desc = models.TextField()
# 	book_edition = models.CharField(max_length=1000)
# 	book_format = models.CharField(max_length=1000)
# 	book_isbn = models.IntegerField()
# 	book_pages = models.CharField(max_length=500)
# 	book_rating = models.DecimalField(..., max_digits=10, decimal_places=2)
# 	book_rating_count = models.IntegerField()
# 	book_review_count = models.IntegerField()
# 	book_title = models.TextField()
# 	genres = models.TextField()
# 	image_url = models.CharField(max_length=1000)

# class MultiThreading(threading.Thread):
#     def __init__(self, conn, cur, data_to_deal):
# 	    threading.Thread.__init__(self)
# 	    self.threadID = threadID
# 	    self.conn = conn
# 	    self.cur = cur
# 	    self.data_to_deal

# Return all rows from a cursor as a namedtuple
def namedtuplefetchall(cursor):
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

# convert list item to dictionary with book keys
def convert_to_dict(result):
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
            'image': r.image_url
        }
        for r in result
    ]
	return result

# return critically acclaimed books with high ratings and number of ratings
def get_books_homepage():
    with connection.cursor() as cursor:
    	cursor.execute("""
    		SELECT * FROM 
				(SELECT * FROM book_data
				GROUP BY book_title 
				ORDER BY book_rating_count
			    DESC limit 10000) AS A  
			ORDER BY A.book_rating 
			DESC limit 1000""")
    	list_result = namedtuplefetchall(cursor)
    	dict_result = convert_to_dict(list_result)
    return dict_result

# Natural Language Full-text Search
def get_search_results(**kwargs):
	searchitems = kwargs.get('results')
	with connection.cursor() as cursor:
		cursor.execute("""
    		SELECT * FROM book_data
			WHERE MATCH (book_title, book_authors)
			AGAINST (%s IN NATURAL LANGUAGE MODE)
			limit 50""", [searchitems])
		list_result = namedtuplefetchall(cursor)
		dict_result = convert_to_dict(list_result)
	return dict_result

# Natural Language Full-text Search
def get_nlpsearch_results(**kwargs):
	searchitems = kwargs.get('results')
	with connection.cursor() as cursor:
		cursor.execute("""
    		SELECT * FROM book_data
			WHERE MATCH (book_desc)
			AGAINST (%s IN NATURAL LANGUAGE MODE)
			limit 50""", [searchitems])
		list_result = namedtuplefetchall(cursor)
		dict_result = convert_to_dict(list_result)
	return dict_result


# get all details of books given book ID
def get_book_details(**kwargs):
	print("Get_Book_Details assigned to thread: {}".format(threading.current_thread().name))
	pk = kwargs.get('pk')
	with connection.cursor() as cursor:
		cursor.execute("""
    		SELECT * FROM book_data  
			WHERE book_id = %s""", [pk])
		list_result = namedtuplefetchall(cursor)
		dict_result = convert_to_dict(list_result)
	return dict_result


# Get books by same author(s) based on given Book ID
def get_same_author_books(**kwargs):
	print("Get_Same_Author_Books assigned to thread: {}".format(threading.current_thread().name))
	pk = kwargs.get('pk')
	with connection.cursor() as cursor:
		cursor.execute("""
    		SELECT DISTINCT A.* FROM book_data AS A
			INNER JOIN 
				(SELECT * FROM book_data
			    WHERE book_id = '%s') AS B 
			ON (A.book_authors like CONCAT('%%',B.book_authors,'%%')
			OR B.book_authors like CONCAT('%%',A.book_authors,'%%'))
			AND NOT A.book_id = '%s' LIMIT 10""", [pk,pk])		
		list_result = namedtuplefetchall(cursor)
		dict_result = convert_to_dict(list_result)
	return dict_result

# Get books by same genre(s) based on given Book ID
def get_same_genre_books(**kwargs):
	print("Get_Same_Genre_Books assigned to thread: {}".format(threading.current_thread().name))
	pk = kwargs.get('pk')
	with connection.cursor() as cursor:
		cursor.execute("""
    		SELECT DISTINCT A.* FROM book_data AS A
			INNER JOIN 
				(SELECT * FROM book_data
			    WHERE book_id = '%s') AS B 
			ON (A.genres like CONCAT('%%',B.genres,'%%')
			OR B.genres like CONCAT('%%',A.genres,'%%'))
			AND NOT A.book_id = '%s' AND NOT A.genres = ''
			LIMIT 7""", [pk,pk])		
		list_result = namedtuplefetchall(cursor)
		dict_result = convert_to_dict(list_result)
	return dict_result



## UNUSED
# def get_book_details_list(**kwargs):
# 	pk = kwargs.get('pk')
# 	with connection.cursor() as cursor:
# 		cursor.execute("""
#     		SELECT * FROM book_data  
# 			WHERE book_id = %s""", [pk])
# 		list_result = cursor.fetchone()
# 	print(list_result)
# 	return list_result

# writing raw sql queries: 
# https://docs.djangoproject.com/en/dev/topics/db/sql/#django.db.models.Manager.raw
