from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView
from multiprocessing.pool import ThreadPool
from django.core.paginator import Paginator
from .models import get_books_homepage, get_book_details
from .models import	get_search_results, get_same_author_books, get_same_genre_books, get_nlpsearch_results
from .nlp_bookdata import get_nlpbook_recommendations

import time

# Create your views here.
def home(request):
	# call critically acclaimed query
	books = get_books_homepage()
	# paginate all book returns
	paginator = Paginator(books, 10)
	page = request.GET.get('page')
	books = paginator.get_page(page)
	# set books up as list
	context = {
		'books': books
	}
	return render(request, 'home/home.html', context)


def book(request, pk):	
	start = time.time()
	pool = ThreadPool(processes=3)
	async_result1 = pool.apply_async(get_book_details,kwds={'pk': pk})
	async_result2 = pool.apply_async(get_same_author_books,kwds={'pk': pk}) 
	async_result3 = pool.apply_async(get_same_genre_books,kwds={'pk': pk})
	context = {
		# Multi-threaded calls
		'books': async_result1.get(),
		'recommendations': async_result2.get(),
		'genres': async_result3.get()
		# Non-threaded calls
		# 'books': get_book_details(pk=pk),
		# 'recommendations': get_same_author_books(pk=pk),
		# 'genres': get_same_genre_books(pk=pk)
	}
	end = time.time()
	print("The time it took to run these threads was {}".format(end-start))
	return render(request, 'home/book.html', context)


def nlpbook(request, pk):	
	start = time.time()
	pool = ThreadPool(processes=3)
	async_result1 = pool.apply_async(get_book_details,kwds={'pk': pk})
	async_result2 = pool.apply_async(get_nlpbook_recommendations,kwds={'pk': pk}) 

	context = {
		'books': async_result1.get(),
		'recommendations': async_result2.get()
	}
	end = time.time()
	print("The time it took to run these threads was {}".format(end-start))
	return render(request, 'home/nlpbook.html', context)

# def search(request):
# 	query = request.GET.get('results')
# 	if query:
# 		context = {
# 			'books': get_search_results(results=query),
# 		}
# 		return render(request, 'home/search.html', context)
# 	return render(request, 'home/search.html', {'init': 'init', 'title': 'Search'},)

def search(request):
	query = request.GET.get('results')
	if query:
		page = request.GET.get('page', 1)
		books = get_search_results(results=query)
		# paginate all book returns
		paginator = Paginator(books, 10)
		books = paginator.get_page(page)
		context = {
			'books': books,
			'query': query,
		}
		return render(request, 'home/search.html', context)
	return render(request, 'home/search.html', {'init': 'init', 'title': 'Search'},)

def nlpsearch(request):
	query = request.GET.get('results')
	if query:
		page = request.GET.get('page', 1)
		books = get_nlpsearch_results(results=query)
		# paginate all book returns
		paginator = Paginator(books, 10)
		books = paginator.get_page(page)
		context = {
			'books': books,
			'query': query,
		}
		return render(request, 'home/nlpsearch.html', context)
	return render(request, 'home/nlpsearch.html', {'init': 'init', 'title': 'Search'},)

def about(request):
	return render(request, 'home/about.html', {'title': 'About'})
