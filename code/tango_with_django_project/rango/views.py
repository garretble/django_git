from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

from datetime import datetime


def decode_url(url):
    ''' Takes string and either removes or places underscores to toggle between URL or plain text.
        str -> str
        
        decode_url('test_url') -> 'test url'
        decode_url('test url') -> 'test_url'
    '''
    if '_' in url:
        return url.replace('_',' ')
    else:
        return url.replace(' ','_')


def index(request):
    
    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)
    
    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template.
    
    
    # Query database for a list of ALL categories currestly stored.
    # Order the categories by number of likes is descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list i our context_dict dictionary whih will be passed to the template engine
    
    category_list = Category.objects.order_by('-likes')[:5]
    pages_list = Page.objects.order_by('-views')[:5]
    context_dict = { 'boldmessage': "There are no categories present.",
                    'cat_urls' : [],
                    'categories': category_list,
                    'pages':pages_list,}
    
    
    
    # We loop through each category returned, and create a URL attribute
    # This attribute stores an encoded URL (e.g. spaces replaced with underscores)
    for category in category_list:
        category.url = decode_url(category.name)
        context_dict['cat_urls'].append(category.url)
    

    # Does the cookie last_visit exist?
    if request.session.get('last_visit'):
        # The session has a value for the last visit
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits',0)

        # If it's been more than a day since the last visit...
        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits'] = visits+1
            request.session['last_visit'] = str(datetime.now())
    else:
        # The get returns None, and the session does not have a value for the last visit.
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1
    
    
    # Return response back to the user
    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    context = RequestContext(request)
    context_dict = { 'boldmessage': "You are on the about page, sucka!"}
    if request.session.get('visits'):
        context_dict['visits'] = request.session.get('visits')
    else:
        context_dict['visits'] = 0
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
    # Request our context from the request passed to us.
    context = RequestContext(request)
    
    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
    category_name = decode_url(category_name_url)
    
    # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
    context_dict = {'category_name': category_name,
                    'category_name_url':category_name_url}
    
    try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(name=category_name)
        
        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category)
        
        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category

    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        context_dict['error'] = 'Category Exception'
    
    # Go render the response and return it to the client.
    return render_to_response('rango/category.html', context_dict, context)

def add_category(request):
    # Get the context from the request
    context = RequestContext(request)
    
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        
        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)
            
            # Now call the index() view
            # The user will be shown the homepage
            return index(request)
        else:
            # The supplied fom contained errors - just print them to the terminal
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details
        form = CategoryForm()
        
    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', {'form': form}, context)

def add_page(request, category_name_url):
    context = RequestContext(request)
    
    category_name = decode_url(category_name_url)
    try:
        catty = Category.objects.get(name=category_name)
    except Category.DoesNotExist:
        return render_to_response('rango/add_page.html', {'error':'error'}, context)
    
    if request.method == 'POST':
        form = PageForm(request.POST)
        
        if form.is_valid():
            # This time we cannot commit straight away
            # Not all fields are automatically populated!
            page = form.save(commit=False)
            
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                # If we get here, the Category does not exist.
                # We render the add_page.html template without a context dictionary
                # This will trigger the red text to appear in the template!
                return render_to_response('rango/add_page.html', {'bonk':"bonk"}, context)
            
            # Also, create a default value for the number of views.
            page.views = 0
            
            # With this, we can then save our new model instance.
            page.save()
            
            # Now that the page is saved, display the category instead
            return category(request, category_name_url)
        else:
            print form.errors
            
    else:
        form = PageForm()
        
    return render_to_response( 'rango/add_page.html', 
                              {'category_name_url': category_name_url,
                               'category_name': category_name, 'form': form},
                              context)

def register(request):
    
    # Like before, get the request's context
    context = RequestContext(request)
    
    # A boolean value for telling the template whether the registration was successful.
    # set to False initially. Code changes value to True when registration succeeds.
    registered = False
    
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab informaiton from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)
        
        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()
            
            # Now we hash the password with the set_password method
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()
            
            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user
            
            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            
            # Now we save the UserProfile model instance.
            profile.save()
            
            # Update our variable to tell the template registration was successful.
            registered = True
        
        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors
    
    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    
    # Render the template depending on the context.
    return render_to_response('rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered}, context)

def user_login(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)
    
    # If the request is a HTTP POST, try to pull out the relevant information
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']
        
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is
        user = authenticate(username=username, password = password )
        
        # If we have a User object, the details are correct
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user is not None:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")
    
    # The request is not a HTTP POST, so display the login form
    # This scenario would most likely be HTTP GET.
    else:
        # No content variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('rango/login.html', {}, context)

@login_required
def restricted(request):
    context = RequestContext(request)
    return render_to_response('rango/restricted.html', {}, context)

@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out
    logout(request)
    
    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')