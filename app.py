from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
import requests
import time


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_headers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
        "DNT": "1"
    }
    return headers

def build_url(search_query):
    search_query = search_query.replace(' ', '+')
    base_url = 'https://www.amazon.com/s?k={0}'.format(search_query)
    return base_url

def extract_product_info(result):
    asin = result['data-asin']
    product_name = result.h2.text

    try:
        img_url = result.find('img', {'class': 's-image'})['src']
    except AttributeError:
        img_url = ""

    try:
        rating = result.find('i', {'class': 'a-icon'}).text
        rating_count = result.find_all('span', {'aria-label': True})[1].text
    except AttributeError:
        return None

    try:
        price1 = result.find('span', {'class': 'a-price-whole'}).text
        price2 = result.find('span', {'class': 'a-price-fraction'}).text
        price = float((price1 + price2).replace(',', ''))
        product_url = 'https://amazon.com' + result.h2.a['href']
    except AttributeError:
        return None

    return product_name, rating, rating_count, price, product_url, img_url, asin

def scrape_de_price(asin, product_name):
    headers = get_headers()
    base_url = f'https://www.amazon.de/dp/{asin}'
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    if "404 - Datei oder Verzeichnis wurde nicht gefunden" in str(soup):
        search_query = product_name.replace(' ', '+')
        base_url = f'https://www.amazon.de/s?k={search_query}'
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

    try:
        price1 = soup.find('span', {'class': 'a-price-whole'}).text
        price2 = soup.find('span', {'class': 'a-price-fraction'}).text
        price = float((price1 + price2).replace(',', '.'))
    except AttributeError:
        price = None

    return price


def scrape_top_10_products(search_query):
    headers = get_headers()
    items = []
    item_count = 0

    url = build_url(search_query)
    print('Processing {0}...'.format(url))
    response = requests.get(url, headers=headers)
    time.sleep(5)  # Add a delay of 5 seconds between requests
    print('Status code:', response.status_code)  # Add this line to print the status code
    soup = BeautifulSoup(response.content, 'html.parser')

    results = soup.find_all('div', {'class': 's-result-item', 'data-component-type': 's-search-result'})

    for result in results:
        if item_count >= 10:
            break

        product_info = extract_product_info(result)
        if product_info:
            items.append(product_info)
            item_count += 1

    return items

@app.get("/", response_class=HTMLResponse)
async def search(request: Request):
    img_url = "/static/logo.png"
    return templates.TemplateResponse("search.html", {"request": request, "img_url": img_url})


@app.post("/result", response_class=HTMLResponse)
async def result(request: Request, search_query: str = Form(...)):
    items = scrape_top_10_products(search_query)
    return templates.TemplateResponse("result.html", {"request": request, "items": items, "enumerate": enumerate, "search_query": search_query})

@app.post("/product", response_class=HTMLResponse)
async def product(request: Request, asin: str = Form(...), search_query: str = Form(...)):
    items = scrape_top_10_products(search_query)
    for item in items:
        if item[6] == asin:
            product_name = item[0]
            img_url = item[5]
            price = item[3]
            break

    de_price = scrape_de_price(asin, product_name)

    return templates.TemplateResponse("product.html", {"request": request, "product_name": product_name, "img_url": img_url, "price": price, "asin": asin, "de_price": de_price})


