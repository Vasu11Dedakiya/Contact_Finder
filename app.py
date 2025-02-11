import re
import json
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from flask import Flask, request, render_template

app = Flask(__name__)

# Set your Google Gemini API Key
GEMINI_API_KEY = "AIzaSyB5LdU_W42nICA2gSJYKzsO9X4myn60zR4"
genai.configure(api_key=GEMINI_API_KEY)


def scrape_website(url):
    """Scrapes text content from a given website URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/98.0.4758.102 Safari/537.36"
        ),
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return text


def extract_phone_numbers(text):
    """
    Extracts phone numbers using a highly accurate regex pattern.
    Supports international formats, extensions, and different separators.
    """
    phone_pattern = re.compile(
        r'\+?\d{1,4}[\s\-]?\(?\d{2,5}\)?[\s\-]?\d{2,5}[\s\-]?\d{2,5}(?:[\s\-xXext.]+?\d{1,5})?'
    )

    # Extract all potential phone numbers
    phone_numbers = phone_pattern.findall(text)

    # Remove duplicates and format neatly
    unique_numbers = list(set(phone_numbers))

    return unique_numbers


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        try:
            text = scrape_website(url)
            phone_numbers = extract_phone_numbers(text)

            result_text = "\n".join(phone_numbers) if phone_numbers else "No phone numbers found."

            return render_template('index.html', result=result_text, url=url)
        except Exception as e:
            return render_template('index.html', error=str(e))
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
