import yaml
import pandas as pd
import matplotlib.pyplot as plt
import Codes.mortgage_calculation as mortgage
import Codes.geolocation as geo
import Codes.documentation as doc
import Codes.cash_flow_estimation as cash_flow
import Codes.rent_estimation as rent
import Codes.property_details as prop_details
import os

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    
def get_api_key():
    # Construct the path to the text file located two folders up from the current working directory
    file_path = os.path.join(os.getcwd(), '..', '..', 'API_Key.txt')

    # Read the content of the text file
    with open(file_path, 'r') as file:
        content = file.read()

    # Extract API keys from the content
    api_keys = {}
    for line in content.split('\n'):
        if line:
            key, value = line.split(' = ')
            api_keys[key] = value.strip('"')

    return api_keys

def run_property_assessment(param_file_path):
    parameters = read_yaml(param_file_path)
    street_address = parameters['property_location']['street_address']
    city = parameters['property_location']['city']
    state = parameters['property_location']['state']
    zip_code = parameters['property_location']['zip_code']

    purchase_price = parameters['deal_information']['purchase_price']
    down_payment = parameters['mortgage_information']['down_payment']
    interest_rate = parameters['mortgage_information']['interest_rate']
    tenure_years = parameters['mortgage_information']['tenure_years']
    openai_model = parameters['Generative_AI']['LLM_model']
    amenities = parameters['property_details']['amenities_to_search']

    bedrooms = parameters['property_details']['number_of_bedrooms']
    baths = parameters['property_details']['number_of_bathrooms']
    build_type = parameters['property_details']['type']


    api_keys = get_api_key()
    google_maps_api_key = api_keys['GOOGLE_MAPS_API_KEY']
    openai_api_key = api_keys['OPENAI_API_KEY']
    rentometer_api_key = api_keys['RENTOMETER_API_KEY']
    rapid_api_key = api_keys['RAPID_API_KEY']

    full_address = street_address + ', ' + city + ', ' + state + ' ' + zip_code
    loan_amount = purchase_price - down_payment

    mortgage_result = mortgage.calculate_mortgage(street_address, loan_amount, interest_rate, tenure_years, "Champion Case")
    print(f"Monthly mortgage payment: ${round(mortgage_result, 2)}")

    print("Searched nearby amenities",)
    amenties_results = geo.get_distance_to_amenities(full_address,amenities,google_maps_api_key)

    print("Generating amenity description using OpenAI")
    doc.generate_amenity_description(amenties_results,openai_api_key,openai_model,full_address,street_address)

    print("Estimating flood risk but pending FEMA data import")
    flood_risk_results = geo.estimate_flood_risk(full_address,google_maps_api_key)

    print("Saving street image...")
    geo.save_street_image(street_address,full_address,google_maps_api_key)

    print("Estimating rent from Rentometer and Zillow ...")
    rentometer_results = rent.get_rentometer_estimate(full_address, street_address, bedrooms, baths, build_type, 365, rentometer_api_key)
    zillow_results = rent.get_zillow_rent_estimates(street_address, full_address, build_type, rapid_api_key)  
    # pending combination of rent data from rentometer and zillow

    print("Fetching property details from Zillow...")
    zestimate_history = prop_details.get_zestimate_history(street_address, full_address, rapid_api_key)
    current_zestimate = prop_details.get_current_zestimate(full_address,rapid_api_key)
    prop_details.get_property_images(street_address,full_address, rapid_api_key)
    tax_history = prop_details.price_and_tax_history(street_address, full_address, rapid_api_key)
                            
    print("Assumnig a final rent of $1500")
    final_rent = 1500

    print("Calculating cash flow... (PENDING VALIDATION)")
    cash_flow.calculate_expenses(street_address, final_rent, param_file_path, tenure_years)

    print("Opening the property in Google Maps...")
    geo.open_in_maps(full_address,google_maps_api_key)

    # pending bringing it together in 1 report
    # pending comparison of multiple properties


    
