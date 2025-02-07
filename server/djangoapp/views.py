from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .models import CarModel
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, create_new_review
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/about.html', context)

# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
    return render(request, 'djangoapp/index.html', context) 

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # Redirect to base if logged in
    if request.user.is_authenticated:
        return redirect('djangoapp:index')
    # Do register
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        exists = False
        try:
            User.objects.get(username=username)
            exists = True
        except:
            logger.debug('User is new')
        if not exists:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            login(request, user)
            return redirect('djangoapp:index')
    return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = 'https://cc47b2e6.us-south.apigw.appdomain.cloud/api/dealerships'
        # Get list of dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context['dealerships'] = dealerships
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == 'GET':
        url = 'https://cc47b2e6.us-south.apigw.appdomain.cloud/api/dealerships'
        # Get single dealership from the URL
        dealership = get_dealers_from_cf(url, id=dealer_id)[0]
        url = 'https://cc47b2e6.us-south.apigw.appdomain.cloud/api/reviews'
        # Get reviews from dealer id
        reviews = get_dealer_reviews_from_cf(url, dealerId=dealer_id)
        context['reviews'] = reviews
        context['dealer_id'] = dealer_id
        context['dealer_name'] = dealership.full_name
        # Return a list of reviews
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context = {}
    if request.user.is_authenticated:
        url = 'https://cc47b2e6.us-south.apigw.appdomain.cloud/api/dealerships'
        # Get dealer from the URL
        dealership = get_dealers_from_cf(url, id=dealer_id)[0]
        context['dealer_id'] = dealer_id
        context['dealer_name'] = dealership.full_name
        context['cars'] = CarModel.objects.filter(dealer_id=dealer_id)
        # New review submission
        if request.method == 'POST':
            url = 'https://cc47b2e6.us-south.apigw.appdomain.cloud/api/reviews'
            last_review = get_dealer_reviews_from_cf(url, getLastReview=True)[0]
            review = dict()
            review['id'] = last_review.id
            review['name'] = request.user.username
            review['time'] = datetime.utcnow().isoformat()
            review['dealership'] = dealer_id
            review['review'] = request.POST['content']
            # Only use fields if included
            if request.POST['purchasecheck'] and request.POST['purchasedate']:
                review['purchase'] = True
                review['purchase_date'] = request.POST['purchasedate']
            else:
                review['purchase'] = False
            # Select car chosen
            car = CarModel.objects.get(id=int(request.POST['car']))
            review['car_make'] = car.make.name
            review['car_model'] = car.name
            review['car_year'] = car.year.year
            json_payload = dict()
            json_payload['review'] = review
            print(json_payload)
            review_created = create_new_review(url, json_payload)
            print(review_created)
            return redirect('djangoapp:dealer_details', dealer_id=dealer_id)
        return render(request, 'djangoapp/add_review.html', context)