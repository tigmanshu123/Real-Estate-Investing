import yaml
import pandas as pd
import matplotlib.pyplot as plt
import Codes.mortgage_calculation as mortgage
import Codes.geolocation as geo
import Codes.documentation as doc

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    parameters = read_yaml('parameters.yml')
    property_address = parameters['property_location']['street_address']
    city = parameters['property_location']['city']
    state = parameters['property_location']['state']
    zip_code = parameters['property_location']['zip_code']

    purchase_price = parameters['deal_information']['purchase_price']
    down_payment = parameters['mortgage_information']['down_payment']
    interest_rate = parameters['mortgage_information']['interest_rate']
    tenure_years = parameters['mortgage_information']['tenure_years']
    google_maps_api_key = parameters['API_KEYS']['Google_maps']
    openai_api_key = parameters['API_KEYS']['Open_AI']
    openai_model = parameters['Generative_AI']['LLM_model']
    amenities = parameters['property_details']['amenities_to_search']


    full_address = property_address + ', ' + city + ', ' + state + ' ' + zip_code
    loan_amount = purchase_price - down_payment

    mortgage_result = mortgage.calculate_mortgage(property_address, loan_amount, interest_rate, tenure_years, "Champion Case")

    amenties_results = geo.get_distance_to_amenities(full_address,amenities,google_maps_api_key)
    doc.generate_amenity_description(amenties_results,openai_api_key,openai_model,full_address,property_address)
    flood_risk_results = geo.estimate_flood_risk(full_address,google_maps_api_key)

    geo.open_in_maps(full_address,google_maps_api_key)


if __name__ == "__main__":
    main()
