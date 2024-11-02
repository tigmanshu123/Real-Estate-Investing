import json
import yaml
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import requests
import Codes.property_details as prop_details

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    


def compute_zestimate_trends(street_address, zestimate_data):
    # Convert timestamps to datetime and extract years
    dates = pd.to_datetime([entry['t'] for entry in zestimate_data], unit='s')
    years = dates.year
    values = [entry['v'] for entry in zestimate_data]

    # Create a DataFrame
    df = pd.DataFrame({'Year': years, 'Value': values})

    # Keep only the latest entry for each year
    df = df.groupby('Year').last().reset_index()  # Reset index to ensure 'Year' is a column

    # Set 'Year' as index
    df.set_index('Year', inplace=True)

    # Calculate annualized return for different periods
    def annualized_return(start_value, end_value, periods):
        return ((end_value / start_value) ** (1 / periods) - 1) * 100

    trends = {}
    current_value = df['Value'].iloc[-1]

    for years in [3, 5, 10]:
        past_date = df.index[-1] - years
        if past_date in df.index:
            past_value = df.loc[past_date, 'Value']
            trends[f'{years}yr'] = annualized_return(past_value, current_value, years)
        else:
            trends[f'{years}yr'] = None  # Not enough data for this period
    
    # Create directory if it doesn't exist
    results_dir = os.path.join(street_address, "Results", "JSON")
    os.makedirs(results_dir, exist_ok=True)

    # Export trends to JSON
    json_path = os.path.join(results_dir, "zestimate_trends.json")
    with open(json_path, 'w') as json_file:
        json.dump(trends, json_file, indent=4)



def compute_zestimate_to_purchase_percent(street_address, zestimate, purchase_price):
    
    if isinstance(zestimate, dict):
        zestimate = zestimate.get('value', 0)

    if purchase_price == 0:
        raise ValueError("Purchase price cannot be zero.")
    
    percent = 100 * (zestimate / purchase_price - 1)

    # Create directory if it doesn't exist
    results_dir = os.path.join(street_address, "Results", "JSON")
    os.makedirs(results_dir, exist_ok=True)

    # Export ratio to JSON
    json_path = os.path.join(results_dir, "zestimate_to_purchase_percent.json")
    with open(json_path, 'w') as json_file:
        json.dump({"zestimate_to_purchase_percent": percent}, json_file, indent=4)



def get_school_ratings(street_address,full_address, rapid_api_key):

    url = "https://zillow-com1.p.rapidapi.com/property"

    zpid = prop_details.get_zillow_zpid(full_address, rapid_api_key)

    querystring = {"zpid":zpid}

    headers = {
        "x-rapidapi-key": rapid_api_key,
        "x-rapidapi-host": "zillow-com1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        schools = data.get('schools', [])
        # Filter the required fields
        filtered_schools = [
            {
                'name': school['name'],
                'rating': school['rating'],
                'distance': school['distance'],
                'level': school['level'],
                'type': school['type']
            }
            for school in schools
        ]              
    else:
        schools = []

    # Create directory if it doesn't exist
    results_dir = os.path.join(street_address, "Results", "JSON")
    os.makedirs(results_dir, exist_ok=True)

    # Update the JSON file with filtered data
    json_path = os.path.join(results_dir, "school_ratings.json")
    with open(json_path, 'w') as json_file:
        json.dump({"schools": filtered_schools}, json_file, indent=4)
    



def compute_cocroi(street_address, params_filepath):

    # Load parameters from YAML file
    params = read_yaml(params_filepath)
    closing_cost = (params['deal_information']['purchase_price'] - params['mortgage_information']['down_payment']) * ( params['expense_information']['closing_cost_%_one_time'] / 100 )
    downpayment = params['mortgage_information']['down_payment']
    initial_capex = params['expense_information']['one_time_other_incl_rehab'] + params['expense_information']['capex_rehab_appliances_one_time']   
            
    total_investment = closing_cost + downpayment + initial_capex

    # Load monthly expenses from Excel file
    excel_path = os.path.join(street_address, "Results", "Excels", "monthly_expenses.xlsx")
    monthly_data = pd.read_excel(excel_path)

    # Convert monthly data to annual data
    monthly_data['Year'] = monthly_data['Month'] // 12
    annual_data = monthly_data.groupby('Year').sum().reset_index()

    # Rename "Monthly Cash Flow" column to "Annual Cash Flow"
    annual_data.rename(columns={"Monthly Cash Flow": "Annual Cash Flow"}, inplace=True)

    # Calculate CoCRoI
    annual_data['CoCRoI'] = 100 * annual_data['Annual Cash Flow'] / total_investment
    # Keep only the 'Year' and 'CoCRoI' columns
    annual_data = annual_data[['Year', 'CoCRoI', 'Annual Cash Flow']]
    annual_data['Total Investment'] = total_investment
    
    # Create directory if it doesn't exist
    results_dir = os.path.join(street_address, "Results", "JSON")
    os.makedirs(results_dir, exist_ok=True)

    # Export annual data with CoCRoI to JSON
    json_path = os.path.join(results_dir, "cocroi.json")
    with open(json_path, 'w') as json_file:
        json.dump(annual_data.to_dict(orient='records'), json_file, indent=4)

    return annual_data


def compute_overall_cagr(street_address, params_filepath, full_address,rapid_api_key):

    # Load parameters from YAML file
    params = read_yaml(params_filepath)
    purchase_price = params['deal_information']['purchase_price']
    downpayment = params['mortgage_information']['down_payment']
    appreciation_rate = params['future_assumptions']['annual_appreciation_percent']
    closing_cost = (params['deal_information']['purchase_price'] - params['mortgage_information']['down_payment']) * ( params['expense_information']['closing_cost_%_one_time'] / 100 )
    initial_capex = params['expense_information']['one_time_other_incl_rehab'] + params['expense_information']['capex_rehab_appliances_one_time']  
    sales_cost_percent = params['future_assumptions']['broker_fee_at_sale_percent'] 
            
    total_investment = closing_cost + downpayment + initial_capex


    # Load amortization schedule from Excel file
    amortization_path = os.path.join(street_address, "Results", "Excels", "Amortization Schedule.xlsx")
    amortization_data = pd.read_excel(amortization_path)

    # Initialize home value and add columns for home value and home equity
    current_zestimate = prop_details.get_current_zestimate(full_address,rapid_api_key)
    if current_zestimate is not None and current_zestimate != 0:
        amortization_data['Home Value'] = purchase_price
    else:
        amortization_data['Home Value'] = purchase_price
    
    amortization_data['Home Equity'] = amortization_data['Home Value'] - amortization_data['Remaining Balance']

    # Update home value and home equity over time
    for i in range(1, len(amortization_data)):
        if i % 12 == 0:  # Increase home value every 12 months
            amortization_data.at[i, 'Home Value'] = amortization_data.at[i-1, 'Home Value'] * (1 + appreciation_rate / 100)
        else:
            amortization_data.at[i, 'Home Value'] = amortization_data.at[i-1, 'Home Value']
        amortization_data.at[i, 'Home Equity'] = amortization_data.at[i, 'Home Value'] - amortization_data.at[i, 'Remaining Balance']


    # Load monthly expenses from Excel file
    excel_path = os.path.join(street_address, "Results", "Excels", "monthly_expenses.xlsx")
    monthly_expense_data = pd.read_excel(excel_path)

    # Convert monthly data to annual data
    monthly_expense_data['Year'] = monthly_expense_data.index // 12

    annual_cash_flow = monthly_expense_data.groupby('Year')['Monthly Cash Flow'].sum().reset_index()

    # Merge annual cash flow with annual data
    annual_data = pd.DataFrame({'Year': range(len(amortization_data) // 12)})
    annual_data = pd.merge(annual_data, annual_cash_flow, on='Year', how='left')
    annual_data.rename(columns={"Monthly Cash Flow": "Annual Cash Flow"}, inplace=True)
    annual_data['Home Value'] = amortization_data.groupby(amortization_data.index // 12)['Home Value'].last().values
    annual_data['Home Equity'] = amortization_data.groupby(amortization_data.index // 12)['Home Equity'].last().values
    annual_data['Sales Cost'] = annual_data['Home Value'] * ( sales_cost_percent / 100 )

    # Calculate cumulative annual cash flow
    annual_data['Cumulative Annual Cash Flow'] = annual_data['Annual Cash Flow'].cumsum()

    # Keep only the 'Year', 'Annual Cash Flow', 'Home Value', 'Home Equity', 'Sales Cost', and 'Overall Return' columns
    annual_data['Overall Return'] = annual_data['Cumulative Annual Cash Flow'] + annual_data['Home Equity'] - annual_data['Sales Cost']
    annual_data = annual_data[['Year', 'Cumulative Annual Cash Flow', 'Annual Cash Flow', 'Home Value', 'Home Equity', 'Sales Cost', 'Overall Return']]

    # Calculate overall CAGR
    annual_data['Overall CAGR'] = ((annual_data['Overall Return'] / total_investment) ** (1 / annual_data['Year']) - 1) * 100
    annual_data['Total Investment'] = total_investment

    # Create directory if it doesn't exist
    results_dir = os.path.join(street_address, "Results", "JSON")
    os.makedirs(results_dir, exist_ok=True)

    # Export annual data with Overall CAGR to JSON
    json_path = os.path.join(results_dir, "overall_cagr.json")
    with open(json_path, 'w') as json_file:
        json.dump(annual_data.to_dict(orient='records'), json_file, indent=4)


    return annual_data



def compute_performance_kpis(street_address, params_filepath, full_address,rapid_api_key):
    # Compute CoCRoI
    cocroi_data = compute_cocroi(street_address, params_filepath)
        
    # Compute Overall CAGR
    cagr_data = compute_overall_cagr(street_address, params_filepath, full_address,rapid_api_key)
        
    # Create directory if it doesn't exist
    results_dir = os.path.join(street_address, "Results", "Excels")
    os.makedirs(results_dir, exist_ok=True)
        
    # Create an Excel writer
    excel_path = os.path.join(results_dir, "Performance_KPIs.xlsx")
    with pd.ExcelWriter(excel_path) as writer:
        cocroi_data.to_excel(writer, sheet_name='CoCRoI', index=False)
        cagr_data.to_excel(writer, sheet_name='Overall CAGR', index=False)
        
    # Plot CoCRoI and Overall CAGR
    plt.figure(figsize=(10, 6))
        
    # Plot CoCRoI
    plt.plot(cocroi_data['Year'], cocroi_data['CoCRoI'], label='CoCRoI', marker='o')
        
    # Plot Overall CAGR
    plt.plot(cagr_data['Year'], cagr_data['Overall CAGR'], label='Overall CAGR', marker='x')
        
    plt.xlabel('Year')
    plt.ylabel('Percentage')
    plt.title('CoCRoI and Overall CAGR Over Time')
    plt.legend()
    plt.grid(True)
        
    # Create directory for plots if it doesn't exist
    plots_dir = os.path.join(street_address, "Plots")
    os.makedirs(plots_dir, exist_ok=True)
        
    # Save the plot
    plot_path = os.path.join(plots_dir, "performance_kpis.png")
    plt.savefig(plot_path)
    plt.close()


