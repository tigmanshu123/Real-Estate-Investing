import requests
import sys
import webbrowser
import os
import json

def get_lat_long(address,API_KEY):
    """Use Google Geocoding API to get latitude and longitude of a given address."""
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
    response = requests.get(geocode_url)
    results = response.json()

    if results['status'] == 'OK':
        location = results['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    elif results['status'] == 'REQUEST_DENIED':
        print("Request denied: Check your API key, billing, or API restrictions.")
    elif results['status'] == 'OVER_QUERY_LIMIT':
        print("You have exceeded your request quota for the day.")
    elif results['status'] == 'INVALID_REQUEST':
        print("Invalid request: Ensure the address is formatted correctly.")
    else:
        print(f"Error fetching lat long for the location: {results['status']}")
    
    return None, None

def open_in_maps(address, API_KEY):
    """Open the specified address in Google Maps using its latitude and longitude."""
    lat, lng = get_lat_long(address, API_KEY)

    if lat is not None and lng is not None:
        # Construct the Google Maps URL
        maps_url = f"https://www.google.com/maps?q={lat},{lng}"
        
        # Open the URL in the default web browser
        webbrowser.open(maps_url)
    else:
        print(f"Unable to find the location for the address: {address}")


def get_nearby_places(lat, lng, place_type, API_KEY):
    """Use Google Places API to find nearby amenities of a given type."""
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1500&type={place_type}&key={API_KEY}"
    response = requests.get(places_url)
    places_data = response.json()

    if places_data['status'] == 'OK':
        places = []
        for place in places_data['results']:
            places.append(place['vicinity'])
        return places
    else:
        return []



def get_distance_to_amenities(street_address, property_address, amenities, API_KEY):
    # Geocode the property address to get latitude and longitude
    lat, lng = get_lat_long(property_address, API_KEY)
    if lat is None or lng is None:
        print("Failed to geocode property address.")
        return None

    results = {}
    for amenity in amenities:
        # Use Places API to find nearby amenities of the given type
        nearby_places = get_nearby_places(lat, lng, amenity, API_KEY)

        if nearby_places:
            # Calculate the distance to the first place found (simplifying for this example)
            amenity_address = nearby_places[0].replace(' ', '+')
            property_address_encoded = f"{lat},{lng}"
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={property_address_encoded}&destinations={amenity_address}&key={API_KEY}"

            # Make the request and process the response
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()                

                if (
                    data['status'] == 'OK' and 
                    'rows' in data and len(data['rows']) > 0 and
                    'elements' in data['rows'][0] and len(data['rows'][0]['elements']) > 0 and
                    data['rows'][0]['elements'][0]['status'] == 'OK'
                ):
                    distance_text = data['rows'][0]['elements'][0]['distance']['text']
                    duration_text = data['rows'][0]['elements'][0]['duration']['text']
                    results[amenity] = {
                        'address': nearby_places[0],
                        'distance': distance_text,
                        'duration': duration_text
                    }

                else:
                    results[amenity] = {
                        'address': "NOT_FOUND",
                        'distance': "NOT_FOUND",
                        'duration': "NOT_FOUND"
                    }                    
            except requests.exceptions.RequestException as e:
                print(f"HTTP Request failed for {amenity}: {e}")
    

    # Create directory if it doesn't exist
    os.makedirs(f"{street_address}/Results/JSON", exist_ok=True)
    
    # Save the results to a JSON file
    with open(f"{street_address}/Results/JSON/amenities_distances.json", 'w') as json_file:
        json.dump(results, json_file, indent=4)


def get_elevation(lat, lng, api_key):
    """Use Google Elevation API to get the elevation of a given location."""
    elevation_url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lng}&key={api_key}"
    response = requests.get(elevation_url)
    elevation_data = response.json()

    if elevation_data['status'] == 'OK':
        elevation = elevation_data['results'][0]['elevation']
        return elevation
    else:
        return None

def get_nearby_water_bodies(lat, lng, api_key):
    """Use Google Places API to find nearby water bodies (rivers, lakes, etc.)."""
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=2000&type=natural_feature&keyword=water&key={api_key}"
    response = requests.get(places_url)
    places_data = response.json()

    if places_data['status'] == 'OK':
        water_bodies = []
        for place in places_data['results']:
            water_bodies.append({
                'name': place.get('name', 'Unknown'),
                'address': place.get('vicinity', 'Unknown')
            })
        return water_bodies
    else:
        return []

def get_historical_flood_zone_risk(lat, lng):
    """Placeholder for accessing historical flood risk data."""
    # Ideally, you would use an API such as FEMA's Flood Map Service Center API or a similar data source.
    # For demonstration purposes, we simulate historical flood zone data.
    # Let's assume areas below 100 meters are more likely to be flood-prone for this simulation.
    return "High" if lat < 41.0 else "Moderate"

def get_rainfall_data(lat, lng):
    """Placeholder for accessing historical or average annual rainfall data."""
    # You would use a reliable weather API such as NOAA or similar for this information.
    # For now, let's simulate it based on latitude.
    return "Heavy" if lat < 40.5 else "Moderate"

def estimate_flood_risk(property_address, api_key):
    # Step 1: Geocode the address to get latitude and longitude
    lat, lng = get_lat_long(property_address, api_key)
    if lat is None or lng is None:
        return None

    # Step 2: Get the elevation of the property
    elevation = get_elevation(lat, lng, api_key)
    if elevation is None:
        return None

    # Step 3: Find any nearby water bodies
    nearby_water_bodies = get_nearby_water_bodies(lat, lng, api_key)

    # Step 4: Get historical flood zone data (simulated)
    flood_zone_risk = get_historical_flood_zone_risk(lat, lng)

    # Step 5: Get rainfall data for the region (simulated)
    rainfall_risk = get_rainfall_data(lat, lng)

    # Step 6: Calculate a flood risk score based on the collected data
    flood_risk_score = 0

    # Elevation Risk - lower elevation means higher flood risk
    if elevation < 20:
        flood_risk_score += 4
    elif elevation < 50:
        flood_risk_score += 3
    elif elevation < 100:
        flood_risk_score += 2
    else:
        flood_risk_score += 1

    # Nearby Water Bodies Risk - proximity to water bodies increases flood risk
    if len(nearby_water_bodies) > 0:
        flood_risk_score += 3

    # Historical Flood Zone Risk
    if flood_zone_risk == "High":
        flood_risk_score += 3
    elif flood_zone_risk == "Moderate":
        flood_risk_score += 2

    # Rainfall Risk - heavy rainfall adds to flood risk
    if rainfall_risk == "Heavy":
        flood_risk_score += 3
    elif rainfall_risk == "Moderate":
        flood_risk_score += 2

    # Determine final flood risk level based on score
    if flood_risk_score >= 10:
        flood_risk_level = "High"
    elif 6 <= flood_risk_score < 10:
        flood_risk_level = "Moderate"
    else:
        flood_risk_level = "Low"

    return {
        "elevation": elevation,
        "nearby_water_bodies": nearby_water_bodies,
        "flood_zone_risk": flood_zone_risk,
        "rainfall_risk": rainfall_risk,
        "flood_risk_level": flood_risk_level
    }


# Function to save the street image of the given property
def save_street_image(street_address,address, API_KEY):
    """Save a street view image of the given address using Google Street View API."""
    lat, lng = get_lat_long(address, API_KEY)
    if lat is None or lng is None:
        print("Failed to geocode property address.")
        return

    # Construct the Google Street View URL
    street_view_url = f"https://maps.googleapis.com/maps/api/streetview?size=600x400&location={lat},{lng}&key={API_KEY}"

    # Send a GET request to the Street View API
    response = requests.get(street_view_url)

    if response.status_code == 200:
        # Create directory if it doesn't exist
        os.makedirs(f"{street_address}/Images", exist_ok=True)
        with open(f"{street_address}/Images/{address.replace(' ', '_')}_streetview.jpg", 'wb') as file:
            file.write(response.content)
    else:
        print("Failed to fetch street view image.")

def save_maps_image(street_address, full_address, API_KEY):
    """Save a Google Maps image of the given address using Google Static Maps API."""
    lat, lng = get_lat_long(full_address, API_KEY)
    if lat is None or lng is None:
        print("Failed to geocode property address.")
        return

    # Construct the Google Static Maps URL
    maps_image_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=15&size=600x400&key={API_KEY}"

    # Send a GET request to the Static Maps API
    response = requests.get(maps_image_url)

    if response.status_code == 200:
        # Create directory if it doesn't exist
        os.makedirs(f"{street_address}/Images", exist_ok=True)
        with open(f"{street_address}/Images/mapview.jpg", 'wb') as file:
            file.write(response.content)
    else:
        print("Failed to fetch maps image.")


def save_maps_image(street_address, full_address, API_KEY, zoom_level):

    """Save a high-resolution Google Maps image of the given address using Google Static Maps API."""
    
    # Get latitude and longitude using the geocoding function
    lat, lng = get_lat_long(full_address, API_KEY)
    if lat is None or lng is None:
        print("Failed to geocode property address.")
        return

    # Higher resolution size (max: 640x640 per image, with scale=2 for better quality)
    size = "640x640"
    scale = 2  # This makes the image effectively 1280x1280

    # Additional labels and map type customization (optional parameters)
    map_type = "roadmap"  # Options: roadmap, satellite, terrain, hybrid
    markers = f"color:red|label:P|{lat},{lng}"  # Mark the target location
    labels = "color:blue|size:mid|label:A|{lat},{lng-0.002}"  # Example additional label nearby

    # Construct the Google Static Maps URL with the enhanced settings
    maps_image_url = (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lng}&zoom={zoom_level}&size={size}&scale={scale}"
        f"&markers={markers}&markers={labels}&maptype={map_type}&key={API_KEY}"
    )

    # Send a GET request to the Static Maps API
    response = requests.get(maps_image_url)

    if response.status_code == 200:
        # Create directory if it doesn't exist
        os.makedirs(f"{street_address}/Images", exist_ok=True)
        # Save the image as a high-quality JPG file
        with open(f"{street_address}/Images/mapview.jpg", 'wb') as file:
            file.write(response.content)
    else:
        print("Failed to fetch maps image.")