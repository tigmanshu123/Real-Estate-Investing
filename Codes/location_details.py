import json
import yaml
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
import pdfkit
import openai
from pdfminer.high_level import extract_text


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
    

def get_niche_overall_grade(street_address, zipcode):
    # URL of the page to scrape
    url = f"https://www.niche.com/places-to-live/z/{zipcode}/"

    # Send a GET request to the webpage
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the element containing the rating (modify selector if necessary)
        rating_element = soup.find("div", class_="overall-grade")

        # Extract the rating text if the element is found
        if rating_element:
            rating = rating_element.get_text(strip=True)
            rating = rating.split('grade')[1].split('Overall')[0].strip()

            # Create directory if it doesn't exist
            json_dir = os.path.join(street_address, "Results", "JSON")
            os.makedirs(json_dir, exist_ok=True)

            # Save the rating as a JSON file
            json_path = os.path.join(json_dir, "niche_overall_grade.json")
            with open(json_path, 'w') as json_file:
                json.dump({"niche_overall_grade": rating}, json_file, indent=4)
        else:
            print("Rating not found.")
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")



def get_niche_area_feel(street_address, zipcode, openai_api_key, gpt_model):

    # URL of the page to scrape
    url = f"https://www.niche.com/places-to-live/z/{zipcode}/"

    # Send a GET request to the webpage
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Create directory if it doesn't exist
        temp_files_dir = os.path.join(street_address, "Results", "Temp Files")
        os.makedirs(temp_files_dir, exist_ok=True)

        # Convert HTML to PDF
        pdf_output_path = os.path.join(temp_files_dir, 'niche_webpage.pdf')
        pdfkit.from_string(str(soup), pdf_output_path)
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
    
    def extract_pdf_content(pdf_path):
        try:
            # Extract text from the PDF
            text = extract_text(pdf_path)
            if not text.strip():
                raise ValueError("PDF content is empty or unreadable.")
            return text
        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return ""
    
    openai.api_key = openai_api_key

    # Extract content from the PDF
    context = extract_pdf_content(pdf_output_path)
    if not context:
        return "Failed to extract meaningful content from the PDF."
    
    question = "What is the area feel of the neighborhood?"

    # Use the chat/completions endpoint with GPT-4
    response = openai.ChatCompletion.create(
        model=gpt_model,  # Ensure you have access to GPT-4
        messages=[
            {"role": "system", "content": "You are a helpful assistant who picks the information asked from the provided context."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}\nAnswer:"},
        ],
        max_tokens=1000,
        temperature=0.5,
    )

    # Extract the answer from the response
    answer = response.choices[0].message['content'].strip()

    # Create directory if it doesn't exist
    json_dir = os.path.join(street_address, "Results", "JSON")
    os.makedirs(json_dir, exist_ok=True)

    # Save the answer as a JSON file
    json_path = os.path.join(json_dir, "niche_area_feel.json")
    with open(json_path, 'w') as json_file:
        json.dump({"niche_area_feel": answer}, json_file, indent=4)


def merge_json_files(street_address, json_path1, json_path2, output_json_path):

    json_path1 = os.path.join(street_address, "Results", "JSON", json_path1)
    json_path2 = os.path.join(street_address, "Results", "JSON", json_path2)
    output_json_path = os.path.join(street_address, "Results", "JSON", output_json_path)
    try:
        # Read the first JSON file
        with open(json_path1, 'r') as file1:
            data1 = json.load(file1)
                
        # Read the second JSON file
        with open(json_path2, 'r') as file2:
            data2 = json.load(file2)
                
        # Merge the contents of the two JSON files
        merged_data = {**data1, **data2}
                
        # Write the merged data to the output JSON file
        with open(output_json_path, 'w') as output_file:
            json.dump(merged_data, output_file, indent=4)
                        
        # Delete the original JSON files
        os.remove(json_path1)
        os.remove(json_path2)
        
    except Exception as e:
        print(f"Error merging JSON files: {e}")