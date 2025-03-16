import scrapy
import re
import json
import os
from flask import Flask, jsonify, request
from urllib.parse import urljoin
import google.generativeai as genai
from google.generativeai import GenerativeModel

# Configure Gemini API Key
GEMINI_API_KEY = "your api key"
genai.configure(api_key=GEMINI_API_KEY)
model = GenerativeModel(model_name="gemini-1.5-pro-latest")

class LeadScraper(scrapy.Spider):
    name = "lead_scraper"
    
    start_urls = [
        "https://www.yellowpages.in/"  # Targeting a structured page for scraping
    ]

    def parse(self, response):
        emails = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", response.text))
        phone_numbers = set(re.findall(r"\+?\d{1,4}?\s?-?\(?\d{2,3}\)?\s?-?\d{3,4}-?\d{3,4}", response.text))

        social_links = {
            "LinkedIn": response.xpath("//a[contains(@href, 'linkedin.com')]/@href").getall(),
            "Twitter": response.xpath("//a[contains(@href, 'twitter.com')]/@href").getall(),
            "Facebook": response.xpath("//a[contains(@href, 'facebook.com')]/@href").getall()
        }

        lead_data = {
            "website": response.url,
            "emails": list(emails),
            "phone_numbers": list(phone_numbers),
            "social_links": social_links
        }

        # os.makedirs("output", exist_ok=True)
        # with open("output/leads.json", "w") as file:
        #     file.write(json.dumps(lead_data) + "\n")
        if os.path.exists(file_path) and os.stat(file_path).st_size > 0:
            with open(file_path, "r") as file:
                try:
                    leads = json.load(file)  # Load JSON list
                except json.JSONDecodeError:
                    leads = []  # If corrupt, start fresh
        else:
            leads = []

        leads.append(lead_data)  # Append new data

        # Write back in proper JSON format
        with open(file_path, "w") as file:
            json.dump(leads, file, indent=4)

        yield lead_data

def generate_summary(leads):
    prompt = f"Summarize these leads: {json.dumps(leads)}"
    response = model.generate_content(prompt)
    return response.text if response else "No summary generated."

app = Flask(__name__)

@app.route('/leads', methods=['GET'])
def get_leads():
    try:
        with open("output/leads.json", "r") as file:
            data = [json.loads(line) for line in file]
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "No leads found!"})

@app.route('/leads/summary', methods=['GET'])
def summarize_leads():
    try:
        with open("output/leads.json", "r") as file:
            data = [json.loads(line) for line in file]
        summary = generate_summary(data)
        return jsonify({"summary": summary})
    except FileNotFoundError:
        return jsonify({"error": "No leads found to summarize!"})

if __name__ == '__main__':
    app.run(debug=True)