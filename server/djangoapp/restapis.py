import requests
import json
from os import environ
# import related models here
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth


# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    print(kwargs)
    print("GET from {} ".format(url))    
    try:
        # Call get method of requests library with URL and parameters
        if 'api_key' in kwargs:
            params = dict()
            params["text"] = kwargs["text"]
            params["version"] = kwargs["version"]
            params["features"] = kwargs["features"]
            params["return_analyzed_text"] = kwargs["return_analyzed_text"]
            params["language"] = kwargs["language"]
            response = requests.get(url, headers={'Content-Type': 'application/json'}, params=kwargs, auth=HTTPBasicAuth('apikey', kwargs['api_key']))
        else:
            response = requests.get(url, headers={'Content-Type': 'application/json'}, params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data


# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, json_payload, **kwargs):
    print(kwargs)
    print("POST from {}".format(url))
    try:
        # Call post
        response = requests.post(url, params=kwargs, json=json_payload, 
        headers={'Content-Type': 'application/json'})
    except:
        print('Network exception occured')
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a get_dealers_from_cf method to get dealers from a cloud function
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url, **kwargs)
    if json_result:
        print(json_result)
        # Get the row list in JSON as dealers
        dealers = json_result["rows"]
        # For each dealer object
        for dealer_doc in dealers:
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   dealer_id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)
    return results

# Example
def get_dealers_by_state_from_cf(url, state):
    return get_dealers_from_cf(url, state=state)

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
def get_dealer_reviews_from_cf(url, **kwargs):
    results = []
    # Call get_request with a URL parameter
    json_result = get_request(url, **kwargs)
    # 
    if json_result:
        print(json_result)
        # Get the row list in JSON as dealers
        reviews = json_result["rows"]
        # For each dealer review object
        for review_doc in reviews:
            # Create a DealerReview object with values in `doc` object
            review_obj = DealerReview(car_make=review_doc['car_make'], car_model=review_doc['car_model'], 
            car_year=review_doc['car_year'], id=review_doc['id'], dealership=review_doc['dealership'], 
            name=review_doc['name'], purchase=review_doc['purchase'], purchase_date=review_doc['purchase_date'], 
            review=review_doc['review'], sentiment='N/A')
            review_obj.sentiment = analyze_review_sentiments(review_obj.review)
            results.append(review_obj)
    return results

# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list
def create_new_review(url, review, **kwargs):
    response = post_request(url, json_payload=review, **kwargs)
    return response

# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(text):
    url = environ['API_URL'] + '/v1/analyze'
    response = get_request(url, text=text, version='2021-03-25', 
        features='sentiment', return_analyzed_text='true', 
        language='en', api_key=environ['WATSON_API_KEY'])
    sentiment = response['sentiment']['document']['label']
    return sentiment