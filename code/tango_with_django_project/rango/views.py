from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("<strong>Rango says hello world!</strong><p><a href='/rango/about/'>About</a></p>")

def about(request):
    return HttpResponse("<p>Rango Says: Here is the about page.</p><img src='http://i.imgur.com/5PwraNq.jpg' /><p><a href='/rango/'>Home</a></p>")
