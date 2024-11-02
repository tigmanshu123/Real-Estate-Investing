import json
import yaml
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import requests


def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    
def get_rentometer_estimate(address, street_address, bedrooms, bathrooms, building_type, lookback, api_key):
    """
    Get rental estimates using the Rentometer API and save the results to an Excel file.

    Parameters:
        address (str): Street address (e.g., '123 Main St').
        street_address (str): Street address for the folder name.
        bedrooms (int): Number of bedrooms in the property.
        bathrooms (float): Number of bathrooms in the property.
        building_type (str): Type of building (e.g., 'apartment', 'house').
        lookback (int): Look-back period in months (e.g., 12 for the past year).
        api_key (str): Rentometer API key.

    Returns:
        dict: Dictionary containing rental data or error message if any issue occurs.
    """
    # Rentometer API endpoint
    url = "https://www.rentometer.com/api/v1/summary"

    # URL encode the address
    address = address.replace(' ', '+')

    # Cap bathrooms at 1.5 if it is greater than or equal to 1.5
    if bathrooms >= 1.5:
        bathrooms = 1.5

    # Adjust building type
    if building_type in ["SingleFamily", "Townhouse", "MultiFamily"]:
        building_type = "house"
    else:
        building_type = "apartment"
    
    # Request payload
    payload = {
        "address": address,
        "bedrooms": bedrooms, # 0 for studio, 1 for 1 bedroom, etc.
        "baths": bathrooms, # Restrict listings to those with only 1 bathroom or 1.5+. Valid values are: blank, "1", or "1.5+".
        "look_back_days": lookback, # Oldest listings to consider in the analysis. Default is 365 days. Must be within the range of 90 to 1460 (48 months).
        "api_key": api_key,
        "building_type": building_type # Restrict listings to Apartments/Condos or Houses/Duplexes. Valid values are: blank, "apartment", or "house".
    }

    try:
        # Make the API request
        response = requests.get(url, params=payload)
        response.raise_for_status()  # Raise exception for bad status codes

        # Parse the JSON response
        data = response.json()

        if 'mean' in data:
            # Structure rental data
            rental_data = {
                "address": data.get("address", address),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "bedrooms": data.get("bedrooms", bedrooms),
                "bathrooms": data.get("baths", bathrooms),
                "building_type": data.get("building_type", building_type),
                "lookback": data.get("look_back_days", lookback),
                "average_rent": data.get("mean"),
                "median_rent": data.get("median"),
                "min_rent": data.get("min"),
                "max_rent": data.get("max"),
                "percentile_25": data.get("percentile_25"),
                "percentile_75": data.get("percentile_75"),
                "std_dev": data.get("std_dev"),
                "sample_size": data.get("samples"),
                "radius_miles": data.get("radius_miles"),
                "quickview_url": data.get("quickview_url"),
                "credits_remaining": data.get("credits_remaining"),
                "token": data.get("token"),
                "links": data.get("links")
            }

            # Create directory if it doesn't exist
            results_dir = os.path.join(street_address, "Results/Excels")
            os.makedirs(results_dir, exist_ok=True)

            # Save to Excel with transposed data
            df = pd.DataFrame([rental_data]).T
            excel_path = os.path.join(results_dir, "Rent Estimates.xlsx")
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Rentometer', header=False)

            return rental_data
        else:
            # Handle case where no rental data is available
            return {"error": "No Rentometer rental data available for the given address."}

    except requests.exceptions.RequestException as e:
        # Handle network or API request errors
        return {"error": f"Error fetching rent data: {e}"}


def get_zillow_rent_estimates(street_address, full_address, building_type, rapid_api_key):
    url = "https://zillow-com1.p.rapidapi.com/rentEstimate"

    querystring = {"address": full_address, "d": "0.5", "propertyType": building_type}

    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "zillow-com1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    try:
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()

        if 'rent' in data:
            rental_data = {
                "address": full_address,
                "building_type": building_type,
                "rent_estimate": data.get("rent"),
                "min_rent": data.get("lowRent"),
                "max_rent": data.get("highRent"),
                "currency": "USD",  # Assuming the currency is USD
                "comparable_rentals": data.get("comparableRentals"),
                "percentile_25": data.get("percentile_25"),
                "percentile_75": data.get("percentile_75"),
                "median_rent": data.get("median"),
                "latitude": data.get("lat"),
                "longitude": data.get("long"),
                "skipped_records": data.get("skippedRecords"),
                "source": "Zillow"
            }

            # Create directory if it doesn't exist
            results_dir = os.path.join(street_address, "Results/Excels")
            os.makedirs(results_dir, exist_ok=True)

            # Save to Excel with transposed data
            df = pd.DataFrame([rental_data]).T
            excel_path = os.path.join(results_dir, "Rent Estimates.xlsx")
            if os.path.exists(excel_path):
                with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer:
                    df.to_excel(writer, sheet_name='Zillow', header=False)
            else:
                with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Zillow', header=False)

            return rental_data
        else:
            return {"error": "No Zillow rental data available for the given address."}

    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching rent data: {e}"}
    

def final_rent_estimator(street_address, rentometer_results, zillow_results, params_filepath):
    # Load the YAML file
    params = read_yaml(params_filepath)
    user_rtr_rent = params.get('income_information', {}).get('expected_rent_rtr')
    user_bp_rent = params.get('income_information', {}).get('expected_rent_biggerpockets')

    # Extract relevant data from dictionaries
    rentometer_data = {
        "median_rent": rentometer_results.get("median_rent"),
        "average_rent": rentometer_results.get("average_rent"),
        "percentile_25": rentometer_results.get("percentile_25"),
        "percentile_75": rentometer_results.get("percentile_75")
    }

    zillow_data = {
        "median_rent": zillow_results.get("rent_estimate"),
        "average_rent": zillow_results.get("rent_estimate"),
        "percentile_25": zillow_results.get("percentile_25"),
        "percentile_75": zillow_results.get("percentile_75")
    }

    # Combine data
    combined_data = {
        "median_rent": [],
        "average_rent": [],
        "percentile_25": [],
        "percentile_75": []
    }

    if rentometer_data:
        if rentometer_data["median_rent"] is not None:
            combined_data["median_rent"].append(rentometer_data["median_rent"])
        if rentometer_data["average_rent"] is not None:
            combined_data["average_rent"].append(rentometer_data["average_rent"])
        if rentometer_data["percentile_25"] is not None:
            combined_data["percentile_25"].append(rentometer_data["percentile_25"])
        if rentometer_data["percentile_75"] is not None:
            combined_data["percentile_75"].append(rentometer_data["percentile_75"])
    
    if zillow_data:
        if zillow_data["median_rent"] is not None:
            combined_data["median_rent"].append(zillow_data["median_rent"])
        if zillow_data["average_rent"] is not None:
            combined_data["average_rent"].append(zillow_data["average_rent"])
        if zillow_data["percentile_25"] is not None:
            combined_data["percentile_25"].append(zillow_data["percentile_25"])
        if zillow_data["percentile_75"] is not None:
            combined_data["percentile_75"].append(zillow_data["percentile_75"])

    if user_rtr_rent not in [0, "", None]:
        combined_data["median_rent"].append(user_rtr_rent)
        combined_data["average_rent"].append(user_rtr_rent)
    if user_bp_rent not in [0, "", None]:
        combined_data["median_rent"].append(user_bp_rent)
        combined_data["average_rent"].append(user_bp_rent)

    # Calculate averages
    avg_estimates = {
        "median_rent": sum(filter(None, combined_data["median_rent"])) / len(combined_data["median_rent"]),
        "average_rent": sum(filter(None, combined_data["average_rent"])) / len(combined_data["average_rent"]),
        "percentile_25": sum(filter(None, combined_data["percentile_25"])) / len(combined_data["percentile_25"]),
        "percentile_75": sum(filter(None, combined_data["percentile_75"])) / len(combined_data["percentile_75"])
    }

    # Path to the Excel file
    excel_path = os.path.join(street_address, "Results/Excels", "Rent Estimates.xlsx")

    # Save the combined data to a new sheet
    avg_df = pd.DataFrame([avg_estimates]).T
    with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a') as writer:
        avg_df.to_excel(writer, sheet_name='rentometer_zillow_user_avg_est', header=False)

    # Create directory if it doesn't exist
    json_dir = os.path.join(street_address, "Results/JSON")
    os.makedirs(json_dir, exist_ok=True)

    # Path to the JSON file
    json_path = os.path.join(json_dir, "final_rent_estimates.json")

    # Save the final results to a JSON file
    with open(json_path, 'w') as json_file:
        json.dump(avg_estimates, json_file, indent=4)

    return avg_estimates
