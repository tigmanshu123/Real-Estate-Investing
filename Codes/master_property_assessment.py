import yaml
import pandas as pd
import matplotlib.pyplot as plt
import Codes.mortgage_calculation as mortgage
import Codes.geolocation as geo
import Codes.documentation as doc
import Codes.cash_flow_estimation as cash_flow
import Codes.rent_estimation as rent
import Codes.property_details as prop_details
import Codes.performance_analysis as perf_analysis
import Codes.location_details as loc_details
import os
import time

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

    start_time = time.time()

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

    sp_cagr = parameters['benchmarking']['sp_cagr']
    hy_savings_rate = parameters['benchmarking']['hy_savings_rate']
    
    api_keys = get_api_key()
    google_maps_api_key = api_keys['GOOGLE_MAPS_API_KEY']
    openai_api_key = api_keys['OPENAI_API_KEY']
    rentometer_api_key = api_keys['RENTOMETER_API_KEY']
    rapid_api_key = api_keys['RAPID_API_KEY']

    full_address = street_address + ', ' + city + ', ' + state + ' ' + zip_code
    loan_amount = purchase_price - down_payment
    closing_costs = parameters['expense_information']['closing_cost_%_one_time'] * loan_amount / 100
    initial_investment = down_payment + closing_costs

    print("\n\nInitiating property assessment for:", full_address)

    # Mortgage assessment
    mortgage_result = mortgage.calculate_mortgage(street_address, loan_amount, interest_rate, tenure_years, "Champion_Case")

    # Nearby amenity assessment
    geo.get_distance_to_amenities(street_address,full_address,amenities,google_maps_api_key)

    # Flood risk assessment
    flood_risk_results = geo.estimate_flood_risk(full_address,google_maps_api_key)

    # Rent estimation
    rentometer_results = rent.get_rentometer_estimate(full_address, street_address, bedrooms, baths, build_type, 365, rentometer_api_key)
    zillow_results = rent.get_zillow_rent_estimates(street_address, full_address, build_type, rapid_api_key)
    final_rent = rent.final_rent_estimator(street_address, rentometer_results, zillow_results, param_file_path)
    
    # Property detail assessment
    geo.save_street_image(street_address,full_address,google_maps_api_key)
    zestimate_history = prop_details.get_zestimate_history(street_address, full_address, rapid_api_key)
    current_zestimate = prop_details.get_current_zestimate(full_address,rapid_api_key)
    prop_details.get_property_images(street_address,full_address, rapid_api_key)
    tax_history = prop_details.price_and_tax_history(street_address, full_address, rapid_api_key)
    prop_details.get_property_characteristics(street_address, full_address, rapid_api_key)
                            
    # Cash flow estimation                           
    cash_flow.calculate_expenses(street_address, final_rent['median_rent'], param_file_path, tenure_years, tax_history,mortgage_result)

    # Performance analysis
    perf_analysis.compute_zestimate_trends(street_address, zestimate_history)
    perf_analysis.compute_zestimate_to_purchase_percent(street_address, current_zestimate, purchase_price)
    perf_analysis.get_school_ratings(street_address,full_address, rapid_api_key)
    perf_analysis.compute_performance_kpis(street_address, param_file_path, full_address, rapid_api_key)
    perf_analysis.create_exec_summary_perf_table(street_address, purchase_price)
    perf_analysis.benchmarking_analysis(street_address, initial_investment, sp_cagr, hy_savings_rate)

    # Location details assessment
    loc_details.get_niche_area_feel(street_address, zip_code, openai_api_key, openai_model)
    loc_details.get_niche_overall_grade(street_address, zip_code)
    loc_details.merge_json_files(street_address,'niche_area_feel.json','niche_overall_grade.json','niche_location_assessment.json')

    # Open the location in Google Maps
    geo.save_maps_image(street_address,full_address,google_maps_api_key,zoom_level=14)
    geo.open_in_maps(full_address,google_maps_api_key)

    # Generate the documentation
    doc.generate_all_markdown_files(street_address, openai_api_key, openai_model, full_address, purchase_price, loan_amount)
    doc.generate_appendix(street_address)
    doc.generate_pdf_from_md_files(street_address, full_address, ['Mohmeet Kaur', 'Tigmanshu Goyal'])

    elapsed_time = time.time() - start_time
    mins, secs = divmod(elapsed_time, 60)
    print(f"Property assessment for {full_address} completed in time (mins:secs): {int(mins)}:{int(secs)}")



    
