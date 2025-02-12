import re
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from flask import Flask, request, render_template
import phonenumbers

app = Flask(__name__)

# Set your Google Gemini API Key
GEMINI_API_KEY = "AIzaSyB5LdU_W42nICA2gSJYKzsO9X4myn60zR4"
genai.configure(api_key=GEMINI_API_KEY)


def scrape_website(url):
    """
    Scrapes and returns a BeautifulSoup object from the given website URL.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def extract_phone_numbers(soup):
    """
    Extracts and validates phone numbers using both 'tel:' links and regex-based scanning.
    It uses the phonenumbers library for parsing and validating numbers.
    """
    phone_numbers_set = set()

    # First, extract phone numbers from "tel:" links
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('tel:'):
            number = href[4:].strip()
            try:
                parsed_number = phonenumbers.parse(number, None)
            except Exception:
                try:
                    parsed_number = phonenumbers.parse(number, "US")
                except Exception:
                    continue
            if phonenumbers.is_valid_number(parsed_number):
                formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                phone_numbers_set.add(formatted)

    # Then, scan the visible text using a more general regex pattern.
    text = soup.get_text(separator=' ', strip=True)
    # This pattern looks for sequences of digits and allowed punctuation
    phone_pattern = re.compile(r'\+?\d[\d\s\-\(\)]{8,}\d')
    potential_numbers = phone_pattern.findall(text)

    for num in potential_numbers:
        num = num.strip()
        # Filter out year ranges like "2015-2024"
        if re.match(r'^\d{4}[-–]\d{4}$', num):
            continue
        try:
            parsed_number = phonenumbers.parse(num, None)
        except Exception:
            try:
                parsed_number = phonenumbers.parse(num, "US")
            except Exception:
                continue
        if phonenumbers.is_valid_number(parsed_number):
            formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            phone_numbers_set.add(formatted)

    return list(phone_numbers_set)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        try:
            soup = scrape_website(url)
            phone_numbers = extract_phone_numbers(soup)

            result_text = "\n".join(phone_numbers) if phone_numbers else "No phone numbers found."
            return render_template('index.html', result=result_text, url=url)
        except Exception as e:
            return render_template('index.html', error=str(e))
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
