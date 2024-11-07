import openai
import os
from markdown2 import markdown
import markdown
import pdfkit
from pathlib import Path
import json
import shutil
import glob
from datetime import datetime
from fpdf import FPDF
from PyPDF2 import PdfMerger
import pandas as pd
import json


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
                # Replace '$' with '$'
                line = line.replace('\\$', '$')

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



def create_exec_summary_md(street_address, full_address, purchase_price, loan_amount):
    # Define file paths
    excel_path = os.path.join(street_address, "Results", "Excels", "Exec_Summary_Performance_KPIs.xlsx")
    md_path = os.path.join(street_address, "Documentation", "MD Files", "Executive Summary.md")
    zestimate_path = os.path.join(street_address, "Results", "JSON", "zestimate_to_purchase_percent.json")
    property_characteristics_path = os.path.join(street_address, "Results", "JSON", "property_characteristics.json")
    niche_location_assessment_path = os.path.join(street_address, "Results", "JSON", "niche_location_assessment.json")
    rent_estimates_path = os.path.join(street_address, "Results", "JSON", "final_rent_estimates.json")

    # Load the Excel file
    df = pd.read_excel(excel_path, sheet_name='Executive Summary')

    # Create markdown table for Performance Analysis Summary
    markdown_table = df.to_markdown(index=True)

    # Load JSON data
    with open(zestimate_path, 'r') as file:
        zestimate_data = json.load(file)
    with open(property_characteristics_path, 'r') as file:
        property_characteristics = json.load(file)
    with open(niche_location_assessment_path, 'r') as file:
        niche_location_assessment = json.load(file)
    with open(rent_estimates_path, 'r') as file:
        rent_estimates = json.load(file)

    # Create property and deal details table
    property_details = {
        "Full address": full_address,
        "Purchase Price": f"${purchase_price}",
        "Zestimate to Purchase Price %": f"{round(zestimate_data['zestimate_to_purchase_percent'], 2)}%",
        "Loan Amount": f"${loan_amount}",
        "Bedrooms": property_characteristics.get('Bedrooms', 'N/A'),
        "Bathrooms": property_characteristics.get('Bathrooms', 'N/A'),
        "Year Built": property_characteristics.get('Year Built', 'N/A'),
        "Home Type": property_characteristics.get('Home Type', 'N/A'),
        "Niche Area Feel": niche_location_assessment.get('niche_area_feel', 'N/A'),
        "Niche Overall Grade": niche_location_assessment.get('niche_overall_grade', 'N/A'),
        "Estimated Median Rent": f"${rent_estimates.get('median_rent', 'N/A')}"
    }

    property_details_md = "| Property & Deal Details | Value |\n| --- | --- |\n"
    for key, value in property_details.items():
        property_details_md += f"| {key} | {value} |\n"

    # Write to markdown file
    with open(md_path, 'w') as md_file:
        md_file.write("## Performance Analysis Summary\n")
        md_file.write(markdown_table)
        md_file.write("\n\n\n## Property & Deal Details\n")
        md_file.write(property_details_md)



def generate_all_markdown_files(street_address, openai_api_key, openai_model, full_address, purchase_price, loan_amount):

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
    
    create_exec_summary_md(street_address, full_address, purchase_price, loan_amount)

    post_process_markdown_files(street_address)



def generate_appendix(street_address):

    # Set the working directory to the markdown files directory
    os.chdir(os.path.join(street_address, "Documentation", "MD Files"))

    md_directory = os.getcwd()

    # Create directory if it does not exist
    if not os.path.exists(md_directory):
        os.makedirs(md_directory)

    # Appendix Content
    appendix_content = """
    # Appendix

    **Additional Images:**
    """
    images_directory = os.path.join("..", "..", "Images").replace('\\', '/')
    for image_file in os.listdir(images_directory):
        if image_file.endswith(".jpg") or image_file.endswith(".png"):
            if image_file != "Zillow_Image_1.jpg":
                image_path = os.path.join(images_directory, image_file).replace('\\', '/')
                appendix_content += f"\n![]({image_path})\n"

    appendix_content += f"""
    
    **Legal Disclaimer:**
    The information provided in this document is for informational purposes only and is not intended as legal or financial advice. Please consult a professional for specific advice regarding your investment.
    """
    appendix_file_path = os.path.join(md_directory, "Appendix.md")
    with open(appendix_file_path, 'w') as file:
        file.write(appendix_content)

    # Change the working directory back to one level up from the root
    os.chdir(os.path.join(street_address, "..", "..", "..", ".."))



def create_cover_page(street_address, author_names, full_address):
    cover_pdf_path = "cover_page.pdf"
    
    # Construct the input PDF path
    input_pdf_path = os.path.join(street_address, "Documentation", "PDF Files", f"Investment Property Report - {full_address}.pdf")
    
    # Create the cover page PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Set a light background color
    pdf.set_fill_color(230, 230, 230)  # Light gray background
    pdf.rect(0, 0, 210, 297, 'F')  # Fill the entire page with the background color
    
    # Set the cover title
    pdf.set_font("Helvetica", "B", size=24)
    pdf.set_text_color(0, 51, 102)  # Dark blue text for a professional look
    pdf.cell(200, 40, "Real Estate Investment Analysis Report", ln=True, align="C")
    pdf.ln(10)

    # Author names
    pdf.set_font("Helvetica", size=12)
    pdf.set_text_color(0, 0, 0)  # Black text
    author_text = ", ".join(author_names)
    pdf.cell(200, 10, f"Authors: {author_text}", ln=True, align="C")
    pdf.cell(200, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True, align="C")
    pdf.ln(20)

    # Disclaimer
    pdf.set_font("Helvetica", size=10)
    pdf.cell(200, 10, "(c) All rights reserved", ln=True, align="C")
    pdf.ln(20)
    
    # Add property image if it exists
    image_path = os.path.join(street_address, "Images", "Zillow_Image_1.jpg")
    if not os.path.exists(image_path):
        image_path = os.path.join(street_address, "Images", "Zillow_Image_1.png")
    
    if os.path.exists(image_path):
        pdf.image(image_path, x=40, y=100, w=130)
    else:
        pdf.set_font("Helvetica", size=10)
        pdf.cell(200, 10, "Property image not found", ln=True, align="C")
    
    # Output the cover page PDF
    pdf.output(cover_pdf_path)
    
    # Merge cover page with the original PDF
    merger = PdfMerger()
    merger.append(cover_pdf_path)
    merger.append(input_pdf_path)
    merger.write(input_pdf_path)
    merger.close()
    
    # Clean up temporary cover page
    os.remove(cover_pdf_path)


def generate_pdf_from_md_files(street_address, full_address, author_names):
    # Define directory for Markdown files
    md_directory = os.path.join(street_address, "Documentation", "MD Files")
    pdf_directory = os.path.join(street_address, "Documentation", "PDF Files")

    # Create PDF directory if it does not exist
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)

    # Order of markdown files to be combined
    md_files_order = [
        "Executive Summary.md","Performance Analysis.md", "Cash Flow & Expenses.md", "Mortgage.md", "Location (by Niche).md",
        "Property Characteristics.md", "School Ratings.md", "Nearby Amenity.md", "Tax History.md", "Rent Estimation.md", "Appendix.md"
    ]

    combined_html_content = ""
    toc_html_content = "<h1>Table of Contents</h1><ul>"
    chapter_number = 1

    # Read and convert each markdown file to HTML
    for md_file in md_files_order:
        md_file_path = os.path.join(md_directory, md_file)
        if os.path.exists(md_file_path):
            with open(md_file_path, 'r') as file:
                md_content = file.read()
                # Convert relative image paths to absolute paths using regex
                # md_content = re.sub(r'!\[\]\((.*?)\)', lambda match: f"![]({os.path.abspath(os.path.join(md_directory, match.group(1)))})" if not os.path.isabs(match.group(1)) else match.group(0), md_content)
                # Convert relative image paths to absolute paths
                md_content = md_content.replace('![](', f'![]({os.path.abspath(os.path.join(md_directory, "../../"))}')
                md_content = md_content.replace("\\", "/")
                md_content = md_content.replace("../../", "/")
                html_content = markdown.markdown(md_content, extensions=['extra', 'tables', 'md_in_html'])
                chapter_title = f"Chapter {chapter_number}: {os.path.splitext(md_file)[0]}"
                toc_html_content += f"<li><a href='#chapter{chapter_number}'>{chapter_title}</a></li>"
                combined_html_content += f"<h1 id='chapter{chapter_number}'>{chapter_title}</h1>" + html_content + "<br><br>"
                chapter_number += 1

    toc_html_content += "</ul><br><br>"
    combined_html_content = toc_html_content + combined_html_content

    # Define enhanced CSS styling
    css_content = """
    <style>
    @page {
        size: A4;
        margin: 1in;
    }
    body {
        font-family: 'Times New Roman', serif;
        line-height: 1.8;
        color: #333;
        font-size: 18pt;
    }
    h1 {
        color: #1A5276;
        font-size: 24pt;
        text-align: center;
        border-bottom: 2px solid #1A5276;
        padding-bottom: 10px;
        margin-bottom: 20px;
        page-break-before: always;
    }
    h2 {
        color: #2874A6;
        font-size: 20pt;
        border-bottom: 1px solid #2874A6;
        padding-bottom: 5px;
        margin-bottom: 15px;
    }
    h3, h4 {
        color: #2E86C1;
        font-size: 16pt;
    }
    img {
        display: block;
        margin: 20px auto;
        max-width: 90%;
        border: 1px solid #ddd;
        padding: 5px;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
    }
    p {
        text-align: justify;
        margin-bottom: 15px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }
    table, th, td {
        border: 1px solid #ddd;
    }
    th, td {
        padding: 10px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        color: #333;
    }
    a {
        color: #1A5276;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    </style>
    """

    # Combine HTML content and CSS styling
    final_html_content = f"<!DOCTYPE html><html><head>{css_content}</head><body>{combined_html_content}</body></html>"

    # Define PDFKit options
    options = {
        'quiet': '',
        'enable-local-file-access': ''  # Allows access to local images and resources
    }

    # Generate PDF from combined HTML content with CSS styling
    pdf_file_path = os.path.join(pdf_directory, f"Investment Property Report - {full_address}.pdf")
    try:
        pdfkit.from_string(final_html_content, pdf_file_path, options=options)
    except OSError as e:
        print(f"Error generating PDF: {e}")

    create_cover_page(street_address, author_names, full_address)


