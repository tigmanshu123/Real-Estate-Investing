import yaml
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def calculate_mortgage(street_address, principal, annual_interest_rate, years, scenario_name):

    monthly_interest_rate = annual_interest_rate / 100 / 12
    number_of_payments = years * 12
    monthly_payment = principal * monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments / ((1 + monthly_interest_rate) ** number_of_payments - 1)

    amortization_schedule = []
    remaining_balance = principal

    for month in range(1, number_of_payments + 1):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment
        amortization_schedule.append([month, monthly_payment, principal_payment, interest_payment, remaining_balance])

    # Create the Plots directory if it doesn't exist
    plots_dir = street_address + '/Plots/'
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)

    # Generate the amortization chart
    months = [row[0] for row in amortization_schedule]
    principal_payments = [row[2] for row in amortization_schedule]
    interest_payments = [row[3] for row in amortization_schedule]
    remaining_balances = [row[4] for row in amortization_schedule]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(months, principal_payments, label='Principal Payment', color='tab:blue')
    ax1.plot(months, interest_payments, label='Interest Payment', color='tab:orange')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Amount ($)')
    ax1.tick_params(axis='y')

    ax2 = ax1.twinx()
    ax2.plot(months, remaining_balances, label='Remaining Balance', color='tab:green')
    ax2.set_ylabel('Remaining Balance ($)')
    ax2.tick_params(axis='y')

    fig.suptitle('Amortization Schedule')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax1.grid(True)

    plt.savefig(os.path.join(plots_dir, f'Amortization Schedule - {scenario_name}.png'))
    plt.close()

    # Create the Results directory if it doesn't exist
    results_dir = street_address + '/Results/'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    df = pd.DataFrame(amortization_schedule, columns=["Month", "Monthly Payment", "Principal Payment", "Interest Payment", "Remaining Balance"])

    # Load existing Excel file if it exists
    excel_file_path = os.path.join(results_dir, 'Amortization Schedule.xlsx')
    if os.path.exists(excel_file_path):
        with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:
            if scenario_name in writer.book.sheetnames:
                del writer.book[scenario_name]
            df.to_excel(writer, sheet_name=scenario_name, index=False)
    else:
        with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=scenario_name, index=False)
    
    print("\nThe monthly mortgage payment is: $", monthly_payment)

    return monthly_payment


def main():
    parameters = read_yaml('parameters.yml')

    street_address = parameters['property_location']['street_address']

    try:
        principal = float(parameters['deal_information']['purchase_price']) - float(parameters['mortgage_information']['down_payment'])
        annual_interest_rate = float(parameters['mortgage_information']['interest_rate'])
        years = int(parameters['mortgage_information']['tenure_years'])
    except ValueError as e:
        print(f"Error converting parameters to float: {e}")
        return
       
    monthly_payment = calculate_mortgage(street_address, principal, annual_interest_rate, years,"Champion Case") 
    print(f"Monthly mortgage payment: {round(monthly_payment, 2)}")

    
if __name__ == "__main__":
    main()
