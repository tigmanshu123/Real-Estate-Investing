import yaml
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def calculate_expenses(street_address, final_rent, params_file_path, tenure_in_years):
    params = read_yaml(params_file_path)
    
    expense_information = params.get('expense_information', {})
    future_assumptions = params.get('future_assumptions', {})
    
    vacancy_rate_percent = expense_information.get('vacancy_rate_percent', 0)
    monthly_repair_percent = expense_information.get('monthly_repair_percent', 0)
    monthly_capex_percent = expense_information.get('monthly_capex_percent', 0)
    annual_taxes = expense_information.get('annual_taxes', 0)
    pm_monthly_percent = expense_information.get('pm_monthly_percent', 0)
    pm_turnover_fee_years = expense_information.get('pm_fee_number_of_months', 0)
    no_rent_initial_period_months = expense_information.get('no_rent_initial_period_months', 0)
    number_free_pm_years = expense_information.get('number_free_pm_years', 0)
    annual_insurance = expense_information.get('annual_insurance', 0)
    capex_rehab_appliances_one_time = expense_information.get('capex_rehab_appliances_one_time', 0)
    monthly_water_sewer_garbage = expense_information.get('monthly_water_sewer_garbage', 0)
    monthly_gas_electricity = expense_information.get('monthly_gas_electricity', 0)
    monthly_hoa = expense_information.get('monthly_hoa', 0)
    monthly_snow_removal = expense_information.get('monthly_snow_removal', 0)
    monthly_lawn_care = expense_information.get('monthly_lawn_care', 0)
    monthly_other = expense_information.get('monthly_other', 0)
    one_time_other_incl_rehab = expense_information.get('one_time_other_incl_rehab', 0)
    
    annual_rent_growth_percent = future_assumptions.get('annual_rent_growth_percent', 0)
    annual_tax_growth_percent = future_assumptions.get('annual_tax_growth_percent', 0)
    annual_insurance_growth_percent = future_assumptions.get('annual_insurance_growth_percent', 0)
    annual_water_sewer_garbage_growth_percent = future_assumptions.get('annual_water_sewer_garbage_growth_percent', 0)
    annual_hoa_growth_percent = future_assumptions.get('annual_hoa_growth_percent', 0)

    months = tenure_in_years * 12
    initial_rent = final_rent

    data = {
        'Month': list(range(1, months + 1)),
        'Monthly Rent': [],
        'Monthly Vacancy Cost': [],
        'Monthly Repairs': [],
        'Monthly CapEx': [],
        'Monthly Taxes': [],
        'Monthly Property Management': [],
        'Monthly Insurance': [],
        'Monthly Water/Sewer/Garbage': [],
        'Monthly Gas/Electricity': [monthly_gas_electricity] * months,
        'Monthly HOA': [],
        'Monthly Snow Removal': [monthly_snow_removal] * months,
        'Monthly Lawn Care': [monthly_lawn_care] * months,
        'Monthly Other': [monthly_other] * months,
        'One time CapEx/Rehab/Appliances': [0] * months,
        'One time Other (incl. Rehab)': [0] * months,
        'One Time PM Turnover Fee': [0] * months
    }

    for month in range(1, months + 1):
        year = (month - 1) // 12
        rent = final_rent * ((1 + annual_rent_growth_percent / 100) ** year)
        taxes = (annual_taxes * ((1 + annual_tax_growth_percent / 100) ** year)) / 12
        insurance = (annual_insurance * ((1 + annual_insurance_growth_percent / 100) ** year)) / 12
        water_sewer_garbage = monthly_water_sewer_garbage * ((1 + annual_water_sewer_garbage_growth_percent / 100) ** year)
        hoa = monthly_hoa * ((1 + annual_hoa_growth_percent / 100) ** year)

        if month <= no_rent_initial_period_months:
            rent = 0
            vacancy_cost = 0
        else:
            vacancy_cost = vacancy_rate_percent / 100 * rent

        data['Monthly Rent'].append(rent)
        data['Monthly Vacancy Cost'].append(vacancy_cost)
        data['Monthly Repairs'].append(monthly_repair_percent / 100 * (rent if rent != 0 else initial_rent))
        data['Monthly CapEx'].append(monthly_capex_percent / 100 * (rent if rent != 0 else initial_rent))
        data['Monthly Taxes'].append(taxes)
        data['Monthly Property Management'].append(pm_monthly_percent / 100 * rent if month > number_free_pm_years * 12 else 0)
        data['Monthly Insurance'].append(insurance)
        data['Monthly Water/Sewer/Garbage'].append(water_sewer_garbage)
        data['Monthly HOA'].append(hoa)

    # Include one-time costs
    data['One time CapEx/Rehab/Appliances'][0] = capex_rehab_appliances_one_time
    data['One time Other (incl. Rehab)'][0] = one_time_other_incl_rehab
    data['One Time PM Turnover Fee'][0] = final_rent * pm_turnover_fee_years

    df = pd.DataFrame(data)
    df['Total Monthly Expenses'] = df.drop(columns=['Monthly Rent']).sum(axis=1)
    df['Monthly Cash Flow'] = df['Monthly Rent'] - df['Total Monthly Expenses']

    # Create the Results directory if it doesn't exist
    results_dir = street_address + '/Results/'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Save the results to an Excel file
    results_file_path = os.path.join(results_dir, 'monthly_expenses.xlsx')
    df.to_excel(results_file_path, index=False)

    print(f"Monthly expenses saved to: {results_file_path} but pending check with TG's main Excel")

    # Plotting the data
    plt.figure(figsize=(14, 8))

    # Plot Monthly Rent vs Monthly Cash Flow
    plt.subplot(2, 1, 1)
    plt.plot(df['Month'], df['Monthly Rent'], label='Monthly Rent', color='blue')
    plt.plot(df['Month'], df['Monthly Cash Flow'], label='Monthly Cash Flow', color='green')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.title('Monthly Rent and Cash Flow Over Time')
    plt.legend()
    plt.grid(True)

    # Plot Total Monthly Expenses
    plt.subplot(2, 1, 2)
    plt.plot(df['Month'], df['Total Monthly Expenses'], label='Total Monthly Expenses', color='red')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.title('Total Monthly Expenses Over Time')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()

    # Create the Plots directory if it doesn't exist
    plots_dir = os.path.join(street_address, 'Plots')
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)

    # Save the plot to the Plots directory
    plot_file_path = os.path.join(plots_dir, 'monthly_expenses_plot.png')
    plt.savefig(plot_file_path)
    plt.close()

    # Plotting the data for the first 5 years
    df_first_5_years = df[df['Month'] <= 60]

    plt.figure(figsize=(14, 8))

    # Plot Monthly Rent vs Monthly Cash Flow for first 5 years
    plt.subplot(2, 1, 1)
    plt.plot(df_first_5_years['Month'], df_first_5_years['Monthly Rent'], label='Monthly Rent', color='blue')
    plt.plot(df_first_5_years['Month'], df_first_5_years['Monthly Cash Flow'], label='Monthly Cash Flow', color='green')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.title('Monthly Rent and Cash Flow Over Time (First 5 Years)')
    plt.legend()
    plt.grid(True)

    # Plot Total Monthly Expenses for first 5 years
    plt.subplot(2, 1, 2)
    plt.plot(df_first_5_years['Month'], df_first_5_years['Total Monthly Expenses'], label='Total Monthly Expenses', color='red')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.title('Total Monthly Expenses Over Time (First 5 Years)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()

    # Save the plot for the first 5 years to the Plots directory
    plot_file_path_5_years = os.path.join(plots_dir, 'monthly_expenses_plot_first_5_years.png')
    plt.savefig(plot_file_path_5_years)
    plt.close()

    # Aggregate data by year
    df['Year'] = (df['Month'] - 1) // 12 + 1
    df_yearly = df.groupby('Year').sum().reset_index()

    plt.figure(figsize=(14, 8))

    # Plot Yearly Rent vs Yearly Cash Flow side by side
    plt.subplot(2, 1, 1)
    bar_width = 0.35
    index = df_yearly['Year'] 
    plt.bar(index, df_yearly['Monthly Rent'], bar_width, label='Yearly Rent', color='blue')
    plt.bar(index + bar_width, df_yearly['Monthly Cash Flow'], bar_width, label='Yearly Cash Flow', color='green')
    plt.xlabel('Year')
    plt.ylabel('Amount ($)')
    plt.title('Yearly Rent and Cash Flow Over Time')
    plt.legend()
    plt.grid(True)

    # Plot Total Yearly Expenses
    plt.subplot(2, 1, 2)
    plt.bar(df_yearly['Year'], df_yearly['Total Monthly Expenses'], label='Total Yearly Expenses', color='red')
    plt.xlabel('Year')
    plt.ylabel('Amount ($)')
    plt.title('Total Yearly Expenses Over Time')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()

    # Save the yearly plot to the Plots directory
    plot_file_path_yearly = os.path.join(plots_dir, 'yearly_expenses_plot.png')
    plt.savefig(plot_file_path_yearly)
    plt.close()

    print(f"Yearly expenses plot saved to: {plot_file_path_yearly}")

    print(f"Monthly expenses plot saved to: {plot_file_path}")
    print(f"Monthly expenses plot for first 5 years saved to: {plot_file_path_5_years}")

    print(f"Monthly expenses plot saved to: {plot_file_path}")
