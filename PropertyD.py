import requests
from bs4 import BeautifulSoup
import json
import math
import re
import csv


class PropertyScraper:
    def __init__(self, url):
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        self.session = requests.Session()
        self.script = self.get_script_data()

    def get_script_data(self):  # Here is the script obtained, which contains all the required keys for the API.
        response = self.session.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="lxml")
        script = soup.find('script', id='__NEXT_DATA__').text
        return script

    def get_city_id(self, script):  # City Key is obtained
        cityName = "Dubai" #Here we can changed the city location
        script_json = json.loads(script)
        city_ids = script_json["props"]["pageProps"]["reduxWrapperActionsGIPP"]
        for city_id in city_ids:
            if city_id["type"] == "listings/fetchPropertySEOLinks/fulfilled":
                cities = city_id["payload"]["links"]["browse_in"]["urls"]
                for city in cities:
                    if city["title"] == cityName:
                        return re.search(r"city\.id=(\d+)", city["algolia_params"]["filterString"]).group(1)
        return None

    def get_properties_for_page(self, city_id, page):  # The API is constructed and the result of the request is sent.
        algoliaKey = (re.search(r'"algolia_app_key":"([^"]+)"', self.script)).group(1)
        algoliaId = (re.search(r'"algolia_app_id":"([^"]+)"', self.script)).group(1)
        urlApi = f"https://{algoliaId}-dsn.algolia.net/1/indexes/*/queries?x-algolia-api-key={algoliaKey}&x-algolia-application-id={algoliaId}"
        perPage = 1000
        params = f"page={page}&attributesToHighlight=%5B%5D&hitsPerPage={perPage}&attributesToRetrieve=%5B%22id%22%2C%22category_id%22%2C%22objectID%22%2C%22name%22%2C%22property_reference%22%2C%22price%22%2C%22featured_listing%22%2C%22has_tour_url%22%2C%22has_video_url%22%2C%22is_verified%22%2C%22listed_by%22%2C%22categories%22%2C%22agent%22%2C%22bedrooms%22%2C%22bathrooms%22%2C%22size%22%2C%22neighborhoods%22%2C%22city%22%2C%22building%22%2C%22photos%22%2C%22promoted%22%2C%22tour_360%22%2C%22photos_count%22%2C%22added%22%2C%22video_url%22%2C%22has_dld_history%22%2C%22tour_url%22%2C%22highlighted_ad%22%2C%22has_whatsapp_number%22%2C%22has_agents_whatsapp%22%2C%22has_sms_number%22%2C%22short_url%22%2C%22absolute_url%22%2C%22id%22%2C%22category_id%22%2C%22badges%22%2C%22room_type%22%2C%22uuid%22%2C%22can_chat%22%2C%22is_premium_ad%22%2C%22description_short%22%2C%22_geoloc%22%2C%22completion_status%22%2C%22is_verified_user%22%2C%22agent_profile%22%2C%22payment_frequency%22%2C%22furnished%22%2C%22is_developer_listing%22%5D&facets=%5B%22language%22%5D&filters=(%22city.id%22%3D{city_id})%20AND%20(%22categories_v2.slug_paths%22%3A%22property-for-sale%22)%20AND%20(%22categories_v2.slug_paths%22%3A%22property-for-sale%2Fresidential%2Fvillahouse%22)"
        payload = {
            "requests": [{
                "indexName": "by_verification_feature_asc_property-for-sale-residential.com"
                , "query": "",
                "params": params
            }]
        }
        resp = self.session.post(urlApi, json=payload, headers=self.headers)
        data = resp.json()
        data = data["results"][0]
        return data

    def get_total_properties(self, data):  # The number of properties that can be obtained is analyzed.
        totalProperties = data["nbHits"]
        return totalProperties

    def extract_property_details(self, prop):  # All the desired information is obtained.
        propertyId = prop["id"]
        propertyName = prop["name"]["en"]
        propertyUrl = prop["short_url"]
        propertyDirection = prop["description_short"]
        price = prop["price"]
        imageUri = prop["photos"][0]["main"] if prop["photos"] else "NO Photo"
        bedrooms = prop["bedrooms"]
        bathrooms = prop["bathrooms"]
        result = {
            "PropertyId": propertyId,
            "PropertyUrl": propertyUrl,
            "PropertyName": propertyName,
            "PropertyDirection": propertyDirection,
            "imageUri": imageUri,
            "Price": price,
            "Bedrooms": bedrooms,
            "Bathrooms": bathrooms,
            "WebPage": "Dubizzle"
        }
        return result

    def get_properties(self, city_id):  # All the necessary functions are called to make it work correctly.
        results = []
        perPage = 1000
        page = 0
        data = self.get_properties_for_page(city_id, page)
        totalProperties = self.get_total_properties(data)
        totalRequests = math.ceil(totalProperties / perPage)
        print("TOTAL Properties: ", totalProperties)
        print("Properties per Page: ", perPage)
        print("TOTAL Request: ", totalRequests)
        for page in range(0, totalRequests):
            data = self.get_properties_for_page(city_id, page)
            print(f"Properties found {len(data["hits"])} on page {f"{self.url}&page={page}"}")
            results += [self.extract_property_details(prop) for prop in data["hits"]]
            page += 1
        return results

    # def save_results_to_json(self, results, filename): #JSON Format
    #     with open(filename, 'a') as json_file:
    #         json.dump(results, json_file, indent=4)

    def save_results_to_csv(self, results, filename):  # For CSV Format
        with open(filename, 'a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ["PropertyId", "PropertyUrl", "PropertyName", "PropertyDirection", "imageUri", "Price",
                          "Bedrooms", "Bathrooms", "WebPage"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            # Checking if the CSV file is empty to write the header only once.
            csv_file.seek(0, 2)
            if csv_file.tell() == 0:
                writer.writeheader()
            writer.writerows(results)


# Classes are called
url_page = 'https://uae.dubizzle.com/property-for-sale/residential/villahouse/'
scraper = PropertyScraper(url_page)
script_data = scraper.get_script_data()
city_id = scraper.get_city_id(script_data)
if city_id:
    properties = scraper.get_properties(city_id)
    scraper.save_results_to_csv(properties, 'UAEProperty.csv')
    # scraper.save_results_to_json(properties, 'UAEDubizzle.json')
