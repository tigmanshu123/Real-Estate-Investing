import openai
import os
from markdown2 import markdown
import pdfkit
from pathlib import Path
import json
import shutil
import glob
from datetime import datetime
from fpdf import FPDF


# def convert_md_to_pdf(md_path, md_filename, output_path):
#     """
#     Converts a markdown file to a PDF file using pdfkit.
#     Args:
#         md_path (str): The path to the markdown file.
#         md_filename (str): The name of the markdown file (without extension).
#         output_path (str): The path where the output PDF should be saved.
#     """
#     # Construct the full path to the markdown file
#     path = md_path + '/Documentation/MD Files/'
#     md_file_path = os.path.join(path, md_filename + '.md')

#     # Read the markdown file content
#     with open(md_file_path, 'r') as md_file:
#         md_content = md_file.read()

#     # Convert markdown content to HTML
#     html_content = markdown(md_content, extras=["tables"])

#     # Define a basic CSS style to enhance the PDF appearance
#     css = """
#     body {
#         font-family: Arial, sans-serif;
#         margin: 20px;
#     }
#     h1 {
#         color: #333;
#         border-bottom: 2px solid #ddd;
#         padding-bottom: 10px;
#     }
#     p {
#         line-height: 1.6;
#     }
#     ul, ol {
#         margin: 20px 0;
#         padding-left: 40px;
#     }
#     ul li, ol li {
#         margin: 5px 0;
#     }
#     ul ul, ol ol {
#         margin: 0;
#         padding-left: 20px;
#     }
#     ul li:before {
#         content: "• ";
#         color: #555;
#     }
#     table {
#         width: 100%;
#         border-collapse: collapse;
#         margin: 20px 0;
#     }
#     table, th, td {
#         border: 1px solid #ddd;
#     }
#     th, td {
#         padding: 8px;
#         text-align: left;
#     }
#     th {
#         background-color: #f2f2f2;
#     }
#     """

#     # Combine HTML content with CSS
#     html_with_css = f"<html><head><style>{css}</style></head><body>{html_content}</body></html>"

#     # Convert HTML content to PDF using pdfkit
#     out_path = output_path + '/Documentation/PDF Files/'
#     os.makedirs(out_path, exist_ok=True)
#     pdf_file_path = os.path.join(out_path, md_filename + '.pdf')
    
#     # Define the path to wkhtmltopdf executable (Update the path if needed)
#     path_to_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
#     config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    
#     # Generate the PDF
#     options = {
#         'page-size': 'A4',
#         'margin-top': '0.75in',
#         'margin-right': '0.75in',
#         'margin-bottom': '0.75in',
#         'margin-left': '0.75in',
#         'encoding': "UTF-8",
#         'no-outline': None  # Optional: Remove links from PDF outline
#     }
#     pdfkit.from_string(html_with_css, pdf_file_path, configuration=config, options=options)




def generate_chapter_md(street_address, json_name, chapter_title, openai_api_key, openai_model, base_prompt, system_role):
    # Set up paths
    json_dir = os.path.join(street_address, "Results", "JSON")
    json_file_path = os.path.join(json_dir, json_name)
    md_output_dir = os.path.join(street_address, "Documentation", "MD Files")
    md_file_path = os.path.join(md_output_dir, f"{chapter_title}.md")

    # Create output directory if it does not exist
    Path(md_output_dir).mkdir(parents=True, exist_ok=True)

    # Step 1: Read the JSON
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)

    # Step 2: Generate the final_prompt based on base_prompt and json structure
    json_str = json.dumps(json_data, indent=2)
    final_prompt = f"{base_prompt}\nHere is the JSON structure you will be working with:\n{json_str}"

    # Step 3: Set up OpenAI API and generate response
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": final_prompt}
        ]
    )
    response_content = response.choices[0].message['content']

    # Step 4: Create .md file
    with open(md_file_path, 'w', encoding='utf-8') as md_file:
        # Step 5: Fill the markdown file with response content
        md_file.write(response_content)
    

def append_plot_to_md(street_address, md_filename, plot_name, preceding_text):
    # Create the path to the markdown file
    md_file_path = os.path.join(street_address, 'Documentation', 'MD Files', md_filename)

    # Create the path to the plot file
    plot_path = os.path.join('..', '..', 'Plots', plot_name).replace('\\', '/')

    # Check if the markdown and plot file exists
    if not os.path.exists(md_file_path):
        raise FileNotFoundError(f"The file {md_filename} does not exist in {md_file_path}")

    # Prepare the text to be appended
    text_to_append = f"\n\n{preceding_text}\n\n![]({plot_path})\n"

    # Append the text and plot to the markdown file
    with open(md_file_path, 'a') as md_file:
        md_file.write(text_to_append)



def append_md_files(street_address, md_filenames, final_file_name):
    # Create the path to the final markdown file
    final_file_path = os.path.join(street_address, 'Documentation', 'MD Files', final_file_name)

    with open(final_file_path, 'w') as final_file:
        for md_filename in md_filenames:
            # Create the path to the markdown file
            md_file_path = os.path.join(street_address, 'Documentation', 'MD Files', md_filename)

            # Check if the markdown file exists
            if os.path.exists(md_file_path):
                # Read and append the content to the final file
                with open(md_file_path, 'r') as md_file:
                    final_file.write(md_file.read() + '\n\n')
                
                # Delete the individual markdown file
                os.remove(md_file_path)
            else:
                print(f"The file {md_filename} does not exist in {street_address}")




def post_process_markdown_files(street_address):
    try:
        # Define directory paths
        md_path = os.path.join(street_address, "Documentation", "MD Files")

        # Check if paths exist
        if not os.path.exists(md_path):
            raise FileNotFoundError(f"Markdown directory not found: {md_path}")

        # List of all .md files in the directory
        md_files = [f for f in os.listdir(md_path) if f.endswith('.md')]
        
        # 1. Update all titles in .md files to use '##'
        for md_file in md_files:
            md_file_path = os.path.join(md_path, md_file)
            with open(md_file_path, 'r') as file:
                content = file.readlines()
            
            updated_content = []
            for line in content:
                if line.startswith("#"):
                    line = "##" + line.lstrip("#")
                updated_content.append(line)

            with open(md_file_path, 'w') as file:
                file.writelines(updated_content)


        # Appending md files
        append_md_files(street_address, ['Overall CAGR.md', 'Cash on Cash RoI.md', 'Historical Zestimate Price Trends.md', 'Zestimate History.md', 'Zestimate to Price Delta (%).md'], 'Performance Analysis.md')

        # Add images
        append_plot_to_md(street_address, 'Mortgage.md', 'Amortization_Schedule_Champion_Case.png', 'Below is a chart showing the evolution of the remaining principal, paid interest and remaining balance throughout the mortgage period')
        append_plot_to_md(street_address, 'Cash Flow & Expenses.md', 'monthly_expenses_plot_first_5_years.png', 'Below is a chart showing the evolution of the monthly rent, monthly cash flow and monthly expenses for the first 5 years of ownership')
        append_plot_to_md(street_address, 'Cash Flow & Expenses.md', 'monthly_expenses_plot.png', 'Below is a chart showing the evolution of the monthly rent, monthly cash flow and monthly expenses throughout the ownership tenure')
        append_plot_to_md(street_address, 'Cash Flow & Expenses.md', 'yearly_expenses_plot.png', 'Below is a chart showing the evolution of annual rent, cash flow and expenses throughout the ownership tenure')
        append_plot_to_md(street_address, 'Performance Analysis.md', 'performance_kpis.png', 'Below is a chart showing the evolution of the CoCRoI and Overall CAGR throughout the ownership tenure')
        append_plot_to_md(street_address, 'Performance Analysis.md', 'zestimate_history.png', 'Below is a chart showing the evolution of Zestimate (from Zillow) price of the property over history')
        append_plot_to_md(street_address, 'Tax History.md', 'tax_history.png', 'Below is a chart showing the evolution of the paid tax and assessed value of the property over history (sourced from Zillow)')

    except FileNotFoundError as fnf_error:
        print(f"File not found: {fnf_error}")
    except Exception as e:
        print(f"An error occurred: {e}")



def generate_all_markdown_files(street_address, openai_api_key, openai_model):

    generate_chapter_md(
        street_address=street_address, 
        json_name='amenities_distances.json', 
        chapter_title='Nearby Amenity', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has address, distance, duration of each type of amenity asked by the user for a given real estate investment property. Structure the response in easy-to-read table with the columns Amenity, Address, Distance (in km), Distance (in miles), Duration, Risk Score, Rationale. The Risk Score would range from 1-10 (lowest to highest risk). The Rationale would be a succinct explanation of the risk score for each amenity (anything with a NOT FOUND should be assigned the highest risk score). The rationale and score should reflect a critical and objective description of the property for a proficient real estate investor. Highlight the proximity of nearby amenities and assess any potential risks in the Rationale. As the last row of the table, provide the overall score and rationale for the property. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document. Do not write anything after the table. Write - Below is the risk assessment of the nearby amenities - before the table (nothing else)", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )
    
    generate_chapter_md(
        street_address=street_address, 
        json_name='cocroi.json', 
        chapter_title='Cash on Cash RoI', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the CoCRoI, Annual Cash Flow and Total Investment (till date) for 30 years. Analyze the data and then provide a summary of your overall assessment for the CoCRoI of this potential investment property. Highlight any risks that stand out to you by mentioning specific data points from the json. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )
    
    generate_chapter_md(
        street_address=street_address, 
        json_name='final_rent_estimates.json', 
        chapter_title='Rent Estimation', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the median, average, 25th and 75th percentile of estimated rents across all available sources (Rentometer, Zillow, User inputs). Create a table with 2 columns Type, Estimated Rent to document the data from the json. Analyze the data and then provide a summary of your overall assessment for the estimated rents and the variances/trends across types. Highlight any risks that stand out to you by mentioning specific data points from the json. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )
    
    generate_chapter_md(
        street_address=street_address, 
        json_name='mortgage_amortization.json', 
        chapter_title='Mortgage', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the total monthly payment, principal payment, interest payment and remaining balance for the mortgage on the potential investment property. Analyze the data and then provide a summary of your overall assessment for the mortgage amortization. Highlight any risks that stand out to you by mentioning specific data points from the json. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document. Note that while converting this to a pdf, a chart will also be inserted showing this data visually for the investor", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )
    
    generate_chapter_md(
        street_address=street_address, 
        json_name='niche_location_assessment.json', 
        chapter_title='Location (by Niche)', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the <area feel e.g., Dense Urban, Sparse suburban, etc.> and <overall rating e.g., A+, A, A-, .... D based on crime, housing, family, schools,etc.> for the zipcode of the potential property as mentioned on the Niche website. Create a table to show the 2 values (columns: Assessment Type, Assesment Outcome). Analyze the data and then provide a summary of your overall assessment for the type of location and the tenants it might have. Highlight any risks that stand out to you by mentioning specific data points from the json. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )    

    generate_chapter_md(
        street_address=street_address, 
        json_name='overall_cagr.json', 
        chapter_title='Overall CAGR', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the overall CAGR <overall return /  total investment till date>, Cumulative Cash Flow, Home Value, Home Equity, Sales Cost, Overall return <home equity + cumulative cash flow - sales cost> and Total Investment (till date) for 30 years. Analyze the data and then provide a summary of your overall assessment for the overall CAGR and return of this potential investment property. Highlight any risks that stand out to you by mentioning specific data points from the json. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )
    
    generate_chapter_md(
        street_address=street_address, 
        json_name='price_and_tax_history.json', 
        chapter_title='Tax History', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the tax history of the investment property (among many other data, but you should only look at the tax history). Do not directly mention the time as-is in the .md file, convert it to a year. Analyze the data and then provide a summary of your overall assessment for how the taxes have evolved over history. Highlight any risks that stand out to you by mentioning specific data points from the json. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )
    
    generate_chapter_md(
        street_address=street_address, 
        json_name='property_characteristics.json', 
        chapter_title='Property Characteristics', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the property characteristics of the potential investment property. Convert this information in a tabular format for a .md file, with 2 columns - Characteristic, Value. For characteristics with a NULL value, do include them in the table but write NOT FOUND under Value. Analyze the data and then provide a summary of your overall assessment in a small paragraph below the table. Highlight any risks that stand out to you by mentioning specific data points from the json. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )

    generate_chapter_md(
        street_address=street_address, 
        json_name='school_ratings.json', 
        chapter_title='School Ratings', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has name, rating, distance, level, type for schools in the neighborhood of the given real estate investment property. Structure the response in easy-to-read table with the columns name, rating, distance, level, type. At the bottom of the table (in a separate paragraph), provide a summary of your overall assessment for the property with respect to schools. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document. Write - Below is the risk assessment of the nearby schools - before the table (nothing else)", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )
    
    generate_chapter_md(
        street_address=street_address, 
        json_name='zestimate_history.json', 
        chapter_title='Zestimate History', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has historical evolution of the property price as tracked by Zillow's Zestimate metric. Provide a summary of your overall assessment for the property with respect to how its price has evolved in history. Highlight any risks that you see. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )

    generate_chapter_md(
        street_address=street_address, 
        json_name='zestimate_to_purchase_percent.json', 
        chapter_title='Zestimate to Price Delta (%)', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the percentage difference in Zestimate price and Purchase price for the property after multiplying by 100, e.g., a value of 5.6 would imply that the Zestimate is 5.6 percent higher than the purchase price, which is good as we're buying the property under the market value, and reverse for the opposite case. Add a table with 2 columns - Metric, Value. Write <Zestimate to Purchase price delta (percentage) in Metric and the data in Value rounded to 2 decimals.  Then, below the table provide a summary of your assessment. Highlight any risks that you see. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )

    generate_chapter_md(
        street_address=street_address, 
        json_name='zestimate_trends.json', 
        chapter_title='Historical Zestimate Price Trends', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the historical 3y, 5y, and 10y CAGR price trends for the investment property. Add a table with 2 columns - Time Horizon, CAGR. Write either 3-Year, 5-Year, 10-Year under Time Horizon and the data in CAGR rounded to 2 decimals.  Then, below the table provide a summary of your assessment. Highlight any risks that you see. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )

    generate_chapter_md(
        street_address=street_address, 
        json_name='yearly_cash_flow.json', 
        chapter_title='Cash Flow & Expenses', 
        openai_api_key=openai_api_key, 
        openai_model=openai_model, 
        base_prompt="The attached json has the annual Rental Income, Expenses (Vacancy Cost, Repairs, Capex, Taxes, Property Management, Insurance, Others, One time), Mortgage, Cash Flow, for the anticipated tenure of property ownership. Opine and provide a summary of your in-depth analysis. Specifically, also highlight any interesting discounts/offers for property management or other costs - e.g., is that expense 0 in the first year? What does that imply? Highlight any risks that you see. Finally, make sure that the response is formatted in a way which can be directly pasted in a .md file, and then eventually used to convert in a pdf document.", 
        system_role='You are a highly quantitative and proficient real estate consultant. You refer data in the json to make assessments, and in your assessments you mention the data points that you are referring to as much as possible. Ensure any sub-titles introduced in the response are in bold font and only have 2 ##, no more no less. There should be no titles.'
        )

    post_process_markdown_files(street_address)





