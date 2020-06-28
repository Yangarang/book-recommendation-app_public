from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView
from multiprocessing.pool import ThreadPool
from django.core.paginator import Paginator
from .models import get_books_homepage, get_book_details
from .models import	get_search_results, get_same_author_books, get_same_genre_books

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
	#### OLD UNUSED MULTI-THREADING ####
	# t1 = threading.Thread(target=get_book_details(),args=[pk,], name='t1')
	# t2 = threading.Thread(target=get_recommended_books(),args=[pk,], name='t2')
	# t1.start()
	# t2.start()
	####################
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
		# 'recommendations': get_recommended_books(pk=pk),
	}
	return render(request, 'home/book.html', context)

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

def about(request):
	return render(request, 'home/about.html', {'title': 'About'})
