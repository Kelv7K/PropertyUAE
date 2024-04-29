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

    def get_script_data(self):
        response = self.session.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, features="lxml")
        script = soup.find('script', id='__NEXT_DATA__').text
        return script

    def get_total_properties(self, script):
        script_json = json.loads(script)
        data = script_json["props"]["pageProps"]["searchResult"]
        totalProperties = data["meta"]["total_count"]
        return totalProperties

    def get_properties_for_page(self, page):
        urlPage = f"{self.url}&page={page}"
        resp = self.session.post(urlPage, headers=self.headers)
        soup = BeautifulSoup(resp.text, features="lxml")
        script = soup.find('script', id='__NEXT_DATA__').text
        script_json = json.loads(script)
        data = script_json["props"]["pageProps"]["searchResult"]["listings"]
        return data

    def extract_property_details(self, prop):
        prop = prop["property"]
        propertyId = prop["id"]
        propertyName = prop["title"]
        propertyUrl = prop["share_url"]
        propertyDirection = prop["location"]["full_name"]
        price = prop["price"]["value"]
        imageUri = prop["images"][0]["medium"] if prop["images"] else "NO Photo"
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
            "WebPage": "PropertyFinder"
        }
        return result

    def get_all_properties(self):
        script_data = self.script
        totalProperties = self.get_total_properties(script_data)
        perPage = 25
        totalRequests = math.ceil(totalProperties / perPage)
        print("TOTAL Properties: ", totalProperties)
        print("Properties per Page: ", perPage)
        print("TOTAL Request: ", totalRequests)
        results = []
        for page in range(1, totalRequests + 1):
            data_for_page = self.get_properties_for_page(page)
            print(f"Properties found {len(data_for_page)} on page {f"{self.url}&page={page}"}")
            for prop in data_for_page:
                result = self.extract_property_details(prop)
                results.append(result)
        return results

    # def save_results_to_json(self, results, filename):
    #     with open(filename, 'a') as json_file:
    #         json.dump(results, json_file, indent=4)


    def save_results_to_csv(self, results, filename):
        with open(filename, 'a', newline='', encoding='utf-8') as csv_file:
            fieldnames = ["PropertyId", "PropertyUrl", "PropertyName", "PropertyDirection", "imageUri", "Price",
                          "Bedrooms", "Bathrooms", "WebPage"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Verificar si el archivo CSV está vacío para escribir la cabecera solo una vez
            csv_file.seek(0, 2)  # Ir al final del archivo
            if csv_file.tell() == 0:  # Si el archivo está vacío
                writer.writeheader()

            # Escribir los datos en el archivo CSV
            writer.writerows(results)


# Uso de las clases
url_page = 'https://www.propertyfinder.ae/en/search?l=13&c=2&t=35&fu=0&rp=y&ob=mr'
scraper = PropertyScraper(url_page)
properties = scraper.get_all_properties()
scraper.save_results_to_csv(properties, 'UAEProperty.csv')
# scraper.save_results_to_json(properties, 'UAEPropertyFinder.json')
