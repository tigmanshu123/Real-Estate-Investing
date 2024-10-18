import yaml
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import requests


def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    
def get_zillow_zpid(full_address, rapid_api_key):
    url = "https://zillow56.p.rapidapi.com/search_address"

    querystring = {"address":full_address}

    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "zillow56.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    
    try:
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()

        zpid = data.get("zpid")
        return zpid
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching rent data: {e}"}
    

def get_zestimate_history(street_address, full_address,rapid_api_key):
    url = "https://zillow-com1.p.rapidapi.com/zestimateHistory"

    zpid = get_zillow_zpid(full_address, rapid_api_key)

    querystring = {"zpid":zpid}

    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "zillow-com1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    data = response.json()

    # Extract timestamps and values
    timestamps = [entry['t'] for entry in data]
    values = [entry['v'] for entry in data]

    # Convert timestamps to datetime
    dates = pd.to_datetime(timestamps, unit='s')

    # Create a DataFrame
    df = pd.DataFrame({'Date': dates, 'Value': values})

    # Plot the time series
    plt.figure(figsize=(10, 5))
    plt.plot(df['Date'], df['Value'], marker='o')
    plt.title('Zestimate History')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.grid(True)

    # Create directory if it doesn't exist
    plot_dir = os.path.join(street_address, "Plots")
    os.makedirs(plot_dir, exist_ok=True)

    # Save the plot
    plot_path = os.path.join(plot_dir, "zestimate_history.png")
    plt.savefig(plot_path)
    plt.close()

    return response.json()

def get_current_zestimate(full_address, rapid_api_key):
    url = "https://zillow-com1.p.rapidapi.com/zestimate"

    zpid = get_zillow_zpid(full_address, rapid_api_key)
    querystring = {"zpid":zpid}

    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "zillow-com1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    return response.json()


def get_property_images(street_address,full_address, rapid_api_key):

    url = "https://zillow-com1.p.rapidapi.com/images"

    zpid = get_zillow_zpid(full_address, rapid_api_key)

    querystring = {"zpid":zpid}

    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "zillow-com1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    # Create directory if it doesn't exist
    directory = f"{street_address}/Images"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Extract image URLs from the response
    image_urls = response.json().get('images', [])

    # Download and save each image
    for idx, image_url in enumerate(image_urls):
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            with open(f"{directory}/Zillow_Image_{idx + 1}.jpg", 'wb') as file:
                file.write(image_response.content)


def price_and_tax_history(street_address, full_address, rapid_api_key):

    url = "https://zillow-com1.p.rapidapi.com/priceAndTaxHistory"

    zpid = get_zillow_zpid(full_address, rapid_api_key)

    querystring = {"zpid":zpid}

    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "zillow-com1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    print(data)

    tax_history_df = pd.DataFrame(data['taxHistory'])
    
    tax_history_df['Year'] = pd.to_datetime(tax_history_df['time'], unit='ms').dt.year
    tax_history_df.drop(columns=['time'], inplace=True)

    # Create a plot with Date as the x-axis, and value and taxpaid on two different y-axes
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.set_xlabel('Year')
    ax1.set_ylabel('Value', color='tab:blue')
    ax1.plot(tax_history_df['Year'], tax_history_df['value'], color='tab:blue', marker='o', label='Value')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Tax Paid', color='tab:red')
    ax2.plot(tax_history_df['Year'], tax_history_df['taxPaid'], color='tab:red', marker='x', label='Tax Paid')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    fig.tight_layout()

    # Create directory if it doesn't exist
    plot_dir = os.path.join(street_address, "Plots")
    os.makedirs(plot_dir, exist_ok=True)

    # Save the plot
    plot_path = os.path.join(plot_dir, "tax_history.png")
    plt.savefig(plot_path)
    plt.close()

    return data
