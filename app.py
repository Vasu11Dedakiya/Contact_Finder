import re
import json
import requests
import google.generativeai as genai
import phonenumbers
from bs4 import BeautifulSoup
from flask import Flask, request, render_template
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from pdfminer.high_level import extract_text
import threading

app = Flask(__name__)

# Set your Google Gemini API Key
GEMINI_API_KEY = "AIzaSyB5LdU_W42nICA2gSJYKzsO9X4myn60zR4"
genai.configure(api_key=GEMINI_API_KEY)


def scrape_website(url):
    """Scrapes text content from a given website URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def scrape_with_selenium(url):
    """Uses a headless browser to scrape JavaScript-rendered pages."""
    options = Options()
    options.add_argument("--headless")
    service = Service("chromedriver")  # Ensure you have ChromeDriver installed
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def extract_phone_numbers(text, region="IN"):
    """Extracts and validates phone numbers using the phonenumbers library."""
    phone_numbers = set()

    for match in phonenumbers.PhoneNumberMatcher(text, region):
        if phonenumbers.is_valid_number(match.number):  # Check if it's a valid number
            formatted = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            phone_numbers.add(formatted)

    return list(phone_numbers)


def extract_hidden_api_data(url):
    """Attempts to find phone numbers from hidden APIs."""
    api_endpoints = ["/api/contacts", "/data/phonebook", "/public/phone_list"]
    phone_numbers = []

    for endpoint in api_endpoints:
        response = requests.get(url + endpoint)
        if response.status_code == 200:
            text = json.dumps(response.json())
            phone_numbers.extend(extract_phone_numbers(text))

    return list(set(phone_numbers))


def enumerate_hidden_directories(base_url):
    """Finds phone numbers in hidden directories."""
    directories = ["contacts", "employees", "phonebook", "data", "public"]
    file_types = ["pdf", "txt", "csv", "xlsx"]
    phone_numbers = []

    for directory in directories:
        for file_type in file_types:
            url = f"{base_url}/{directory}/contacts.{file_type}"
            response = requests.get(url)
            if response.status_code == 200:
                text = extract_text(response.content) if file_type == "pdf" else response.text
                phone_numbers.extend(extract_phone_numbers(text))

    return list(set(phone_numbers))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        domain = url.split("//")[-1].split("/")[0]

        results = {"basic_scrape": [], "selenium_scrape": [], "api_search": [], "directory_enum": []}

        threads = [
            threading.Thread(target=lambda: results.update({"basic_scrape": extract_phone_numbers(scrape_website(url))})),
            threading.Thread(target=lambda: results.update({"selenium_scrape": extract_phone_numbers(scrape_with_selenium(url))})),
            threading.Thread(target=lambda: results.update({"api_search": extract_hidden_api_data(url)})),
            threading.Thread(target=lambda: results.update({"directory_enum": enumerate_hidden_directories(url)}))
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        all_phone_numbers = list(set(results["basic_scrape"] + results["selenium_scrape"] +
                                     results["api_search"] + results["directory_enum"]))

        result_text = "📞 Extracted Phone Numbers:\n" + "\n".join(all_phone_numbers) if all_phone_numbers else "No phone numbers found."

        return render_template('index.html', result=result_text, url=url)

    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
