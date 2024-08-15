from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re

application = Flask(__name__)  # Renamed 'app' to 'application'

def extract_values_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Handles HTTP request errors
    except requests.RequestException as e:
        return {"error": f"Failed to retrieve data: {str(e)}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    results = {}

    if tables:
        first_table = tables[0]
        rows = first_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]
            row_text = ' '.join(row_data)

            # Regex extraction of table values
            if "Number of Bays" in row_text:
                number_match = re.search(r'\b(\d+)-Bay\b', row_text)
                results['no_of_bays'] = int(number_match.group(1)) if number_match else None
            
            if "Number of Single Faced Fixed" in row_text:
                number_match = re.search(r'\bNumber of Single Faced Fixed.*?(\d+)$', row_text)
                results['no_of_single_faced_fixed'] = int(number_match.group(1)) if number_match else None

            if "Number of Single Faced Movable" in row_text:
                number_match = re.search(r'\bNumber of Single Faced Movable.*?(\d+)$', row_text)
                results['no_of_single_faced_movable'] = int(number_match.group(1)) if number_match else None

            if "Double Faced" in row_text:
                number_match = re.search(r'\b(?:Double Faced|Dual|Twin Movable).*?(\d+)$', row_text)
                results['no_of_double_faced'] = int(number_match.group(1)) if number_match else None
    else:
        results['error'] = "No tables found on the webpage."

    price_span = soup.find('span', class_='m-w')
    if price_span:
        price = price_span.text.strip()
        results['cost'] = int(float(price.replace('₹', '').replace(',', '')))
    else:
        results['cost'] = None

    if all(v is not None for v in [results.get('cost'), results.get('no_of_bays'), results.get('no_of_single_faced_fixed'), results.get('no_of_single_faced_movable'), results.get('no_of_double_faced')]):
        average = results['cost'] / ((results['no_of_double_faced'] * 2 + results['no_of_single_faced_fixed'] + results['no_of_single_faced_movable']) * results['no_of_bays'])
        results['average'] = round(average,3)
    else:
        results['average'] = "Incomplete data for calculation"

    return results

@application.route('/', methods=['GET', 'POST'])
def home():
    extracted_data = {}
    if request.method == 'POST':
        url = request.form['url']
        extracted_data = extract_values_from_url(url)
    return render_template('index.html', extracted_data=extracted_data)

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)  # Adjusted for production