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
    results_dir = os.path.join(street_address, 'Results')
    os.makedirs(results_dir, exist_ok=True)

    # Create the markdown file path
    file_name = filename + '.md'
    file_path = os.path.join(results_dir, file_name)

    # Write the description to the markdown file with UTF-8 encoding
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f"# Amenity Description for {street_address}\n\n")
        file.write(description)



def convert_md_to_pdf(md_path, md_filename, output_path):
    """
    Converts a markdown file to a PDF file using pdfkit.
    Args:
        md_path (str): The path to the markdown file.
        md_filename (str): The name of the markdown file (without extension).
        output_path (str): The path where the output PDF should be saved.
    """
    # Construct the full path to the markdown file
    path = md_path + '/Results'
    md_file_path = os.path.join(path, md_filename + '.md')

    # Read the markdown file content
    with open(md_file_path, 'r') as md_file:
        md_content = md_file.read()

    # Convert markdown content to HTML
    html_content = markdown(md_content)

    # Convert HTML content to PDF using pdfkit
    out_path = output_path + '/Results'
    pdf_file_path = os.path.join(out_path, md_filename + '.pdf')
    
    # Define the path to wkhtmltopdf executable (Update the path if needed)
    path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    
    # Generate the PDF
    pdfkit.from_string(html_content, pdf_file_path, configuration=config)





# Function to generate property description using OpenAI API
def generate_amenity_description(amenities, openai_api_key, openai_model, property_address, street_address):
    """
    Generates a property description based on nearby amenities using OpenAI's API.
    Args:
        amenities (dict): A dictionary where keys are amenity names and values are dictionaries 
                          containing 'distance' (in km) and 'time' (in mins) to the amenity.
        openai_api_key (str): Your OpenAI API key.
        openai_model (str): The OpenAI model to use for generating the description (e.g., gpt-3.5-turbo or gpt-4).
        property_address (str): The address of the property.
    Returns:
        str: A generated description of the property based on the provided amenities.
    """
    openai.api_key = openai_api_key  # Set the OpenAI API key

    # Construct the prompt based on the amenities dictionary
    prompt = f"Generate a critical and objective description of the property located at {property_address} being assessed given the nearby amenities (their distance and times) for a real estate property investor looking to build their personal rental real estate portfolio. Highlight both the positive aspects and potential risks or downsides. Consider factors that could adversely or positively affect the investment and the associated tenants. State your response like a highly quantitative McKinsey consultant would. Give your response in bullets where each bullet starts with the amenity, and 2 sub bullets - a risk score (with a succinct rationale), and the broader response with data:\n\n"
    for amenity, details in amenities.items():
        prompt += f"{amenity.capitalize()} - Distance: {details['distance']} km, Time: {details['duration']} mins\n"

    # Use the ChatCompletion API
    response = openai.ChatCompletion.create(
        model=openai_model,  # Specify the model (e.g., "gpt-3.5-turbo" or "gpt-4")
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    # Extract and return the generated description
    description = response['choices'][0]['message']['content'].strip()

    save_description_to_markdown(street_address, description, "amenity_description")
    convert_md_to_pdf(street_address,"amenity_description",street_address)

    print("\n\nAmenity description saved to pdf!")






