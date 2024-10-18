import openai
import os
from markdown2 import markdown
import pdfkit

def save_description_to_markdown(street_address, description, filename):
    """
    Saves the given description to a markdown file under the 'Results' folder.
    Args:
        street_address (str): The street address of the property.
        description (str): The description text to be saved in the markdown file.
        filename (str): The name of the markdown file (without extension).
    """
    # Ensure the 'Results' directory exists
    results_dir = os.path.join(street_address, 'Documentation/MD Files')
    os.makedirs(results_dir, exist_ok=True)

    # Create the markdown file path
    file_name = filename + '.md'
    file_path = os.path.join(results_dir, file_name)

    # Write the description to the markdown file with UTF-8 encoding
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f"# Amenity Description for {street_address}\n\n")
        
        # Split the description into lines
        lines = description.split('\n')
        
        # Process each line to format tables correctly
        for line in lines:
            if line.startswith('|') and line.endswith('|'):
                # This is a table row, ensure proper spacing
                file.write(line + '\n')
            else:
                # Regular text
                file.write(line + '\n\n')



def convert_md_to_pdf(md_path, md_filename, output_path):
    """
    Converts a markdown file to a PDF file using pdfkit.
    Args:
        md_path (str): The path to the markdown file.
        md_filename (str): The name of the markdown file (without extension).
        output_path (str): The path where the output PDF should be saved.
    """
    # Construct the full path to the markdown file
    path = md_path + '/Documentation/MD Files/'
    md_file_path = os.path.join(path, md_filename + '.md')

    # Read the markdown file content
    with open(md_file_path, 'r') as md_file:
        md_content = md_file.read()

    # Convert markdown content to HTML
    html_content = markdown(md_content, extras=["tables"])

    # Define a basic CSS style to enhance the PDF appearance
    css = """
    body {
        font-family: Arial, sans-serif;
        margin: 20px;
    }
    h1 {
        color: #333;
        border-bottom: 2px solid #ddd;
        padding-bottom: 10px;
    }
    p {
        line-height: 1.6;
    }
    ul, ol {
        margin: 20px 0;
        padding-left: 40px;
    }
    ul li, ol li {
        margin: 5px 0;
    }
    ul ul, ol ol {
        margin: 0;
        padding-left: 20px;
    }
    ul li:before {
        content: "• ";
        color: #555;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    table, th, td {
        border: 1px solid #ddd;
    }
    th, td {
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
    }
    """

    # Combine HTML content with CSS
    html_with_css = f"<html><head><style>{css}</style></head><body>{html_content}</body></html>"

    # Convert HTML content to PDF using pdfkit
    out_path = output_path + '/Documentation/PDF Files/'
    os.makedirs(out_path, exist_ok=True)
    pdf_file_path = os.path.join(out_path, md_filename + '.pdf')
    
    # Define the path to wkhtmltopdf executable (Update the path if needed)
    path_to_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    
    # Generate the PDF
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None  # Optional: Remove links from PDF outline
    }
    pdfkit.from_string(html_with_css, pdf_file_path, configuration=config, options=options)




# Function to generate property description using OpenAI API
def generate_amenity_description(amenities, openai_api_key, openai_model, property_address, street_address):
    """
    Generates a property description based on nearby amenities using OpenAI's API.
    Args:
        amenities (dict): A dictionary where keys are amenity names and values are dictionaries 
                          containing 'distance' (in km), 'time' (in mins), and 'address' of the amenity.
        openai_api_key (str): Your OpenAI API key.
        openai_model (str): The OpenAI model to use for generating the description (e.g., gpt-3.5-turbo or gpt-4).
        property_address (str): The address of the property.
    Returns:
        str: A generated description of the property based on the provided amenities.
    """
    openai.api_key = openai_api_key  # Set the OpenAI API key

    # Construct the prompt based on the amenities dictionary
    prompt = f"Generate a critical and objective description of the property located at {property_address} for a proficient real estate investor. Highlight the proximity of nearby amenities and assess any potential risks. Provide a risk score with a succinct rationale for each amenity (anything with a NOT FOUND should be assigned the highest risk score). Structure the response in easy-to-read table with the columns Amenity, Address, Distance (in km & miles), Duration, Rationale:\n\n"
    for amenity, details in amenities.items():
        prompt += f"{amenity.capitalize()} - Address: {details['address']}, Distance: {details['distance']} km, Time: {details['duration']} mins\n"

    # Use the ChatCompletion API
    response = openai.ChatCompletion.create(
        model=openai_model,  # Specify the model (e.g., "gpt-3.5-turbo" or "gpt-4")
        messages=[
            {"role": "system", "content": "You are a highly quantitative and proficient real estate consultant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=750
    )

    # Extract and return the generated description
    description = response['choices'][0]['message']['content'].strip()

    save_description_to_markdown(street_address, description, "amenity_description")
    convert_md_to_pdf(street_address, "amenity_description", street_address)







