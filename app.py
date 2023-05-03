from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from typing import Optional
from decimal import Decimal
import re
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed
from database import create_connection
from datetime import datetime
from database import init_db

init_db()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



def fetch_page_content(url):
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    
    driver = webdriver.Chrome(executable_path='/Users/almog/chromedriver/chromedriver', options=chrome_options)
    driver.get(url)
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search")))
    except TimeoutException:
        print("Element not found or it took too long to load the page.")
        driver.quit()
        return None

    page_source = driver.page_source
    driver.quit()
    return page_source



def build_url(search_query):
    search_query = search_query.replace(' ', '+')
    base_url = 'https://www.amazon.com/s?k={0}&language=en_US'.format(search_query)
    return base_url
    
def extract_product_info(result) -> Optional[dict]:
    try:
        title = result.h2.a.text.strip()
    except AttributeError:
        title = None

    try:
        product_url = 'https://amazon.com' + result.h2.a['href']
    except (AttributeError, TypeError):
        product_url = None

    try:
        img_url = result.find('img', {'class': 's-image'})['src']
    except (AttributeError, TypeError):
        img_url = None

    try:
        rating = float(result.find('span', {'class': 'a-icon-alt'}).text.split()[0])
    except (AttributeError, ValueError, IndexError):
        rating = None

    try:
        review_count = int(result.find('span', {'class': 'a-size-base'}).text.replace(',', ''))
    except (AttributeError, ValueError):
        review_count = None

    try:
        price = result.select_one("span.a-price span.a-offscreen").text
    except AttributeError:
        price = None

    if not price:
        try:
            price = result.select_one("span.a-price-range span.a-offscreen").text
        except AttributeError:
            price = None

    if not price:
        try:
            price = result.select_one("span.a-text-price span.a-offscreen").text
        except AttributeError:
            price = None

    try:
        asin = result['data-asin']
    except (AttributeError, KeyError):
        asin = None

    if not title:
        return None

    product_info = {
        'title': title,
        'product_url': product_url,
        'img_url': img_url,
        'rating': rating,
        'review_count': review_count,
        'price': price,
        'asin': asin  # Add the 'asin' field to the product_info dictionary
    }
    return product_info


def get_price_from_url(url: str) -> Optional[str]:
    driver = webdriver.Chrome()
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#productTitle"))
    )

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class, 'a-price') and not(contains(@class, 'a-text-strike'))]")
            )
        )
    except TimeoutException:
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    price_element = soup.select_one("span.a-price:not(.a-text-strike) > span.a-offscreen")
    price = price_element.text.strip() if price_element else None

    return price

def parse_price(price: str) -> Optional[Decimal]:
    if not price:
        return None

    # Extract the number from the price string
    price_number = re.sub(r'[^\d.,]+', '', price)

    # Replace any commas with dots (for consistency)
    price_number = price_number.replace(',', '.')

    return Decimal(price_number)



def scrape_top_10_products(search_query):
    items = []
    item_count = 0

    url = build_url(search_query)
    print('Processing {0}...'.format(url))
    page_content = fetch_page_content(url)
    soup = BeautifulSoup(page_content, 'html.parser')

    results = soup.select("div[data-index]")

    for result in results:
        if item_count >= 10:
            break

        product_info = extract_product_info(result)
        if product_info:
            items.append(product_info)
            item_count += 1

    return items

def convert_to_usd(amount: Decimal, currency: str) -> Optional[Decimal]:
    exchange_rates = {
        "CAD": 0.74,  # 1 CAD = 0.74 USD (as of May 2023)
        "EUR": 1.10,  # 1 EUR = 1.10 USD (as of May 2023)
        "GBP": 1.25   # 1 GBP = 1.25 USD (as of May 2023)
    }

    if currency in exchange_rates:
        usd_amount = amount * Decimal(str(exchange_rates[currency]))
        return usd_amount

    return None


def fetch_price(domain, asin):
    url = get_product_url(asin, domain)
    try:
        price = get_price_from_url(url)
    except Exception as e:
        print(f"Error fetching price for domain: {domain}, Error: {e}")
        price = None
    return url, price, domain




def get_product_url(asin, domain):
    product_url = f'https://{domain}/dp/{asin}'
    return product_url

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
        if item['asin'] == asin:
            product_name = item['title']
            img_url = item['img_url']
            price = item['price']
            rating = item['rating']
            product_urlcom = item['product_url']
            break

    amazon_domains = ['amazon.ca', 'amazon.de', 'amazon.co.uk']
    currencies = {'amazon.ca': 'CAD', 'amazon.de': 'EUR', 'amazon.co.uk': 'GBP'}
    product_urls = {}
    prices = {domain: None for domain in amazon_domains}
    price_not_found = {domain: False for domain in amazon_domains}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(fetch_price, domain, asin) for domain in amazon_domains]

        for future in as_completed(futures):
            try:
                domain, fetched_price, fetched_domain = future.result()
                if fetched_price is not None:
                    price_in_usd = convert_to_usd(parse_price(fetched_price), currencies[fetched_domain])
                    prices[fetched_domain] = price_in_usd
                else:
                    price_not_found[fetched_domain] = True

                product_urls[fetched_domain] = f'https://{fetched_domain}/dp/{asin}'
            except Exception as e:
                print(f"Error fetching price for domain: {fetched_domain}, Error: {e}")

    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''INSERT INTO product_data (query, timestamp, item_name, com_price, co_uk_price, de_price, ca_price)
                  VALUES (?, ?, ?, ?, ?, ?, ?)''',
               (search_query,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                product_name,
                float(parse_price(price)) if price is not None else None,
                float(prices.get('amazon.co.uk', None)) if prices.get('amazon.co.uk', None) is not None else None,
                float(prices.get('amazon.de', None)) if prices.get('amazon.de', None) is not None else None,
                float(prices.get('amazon.ca', None)) if prices.get('amazon.ca', None) is not None else None))

    conn.commit()
    conn.close()
       
    return templates.TemplateResponse("product.html", {
        "request": request,
        "product_name": product_name,
        "product_urlcom": product_urlcom,
        "img_url": img_url,
        "price": price,
        "asin": asin,
        "rating": rating,
        "ca_price": prices.get('amazon.ca', None),
        "de_price": prices.get('amazon.de', None),
        "co_uk_price": prices.get('amazon.co.uk', None),
        "ca_url": product_urls.get('amazon.ca', None),
        "de_url": product_urls.get('amazon.de', None),
        "co_uk_url": product_urls.get('amazon.co.uk', None),
        "ca_not_found": price_not_found.get('amazon.ca', False),
        "de_not_found": price_not_found.get('amazon.de', False),
        "co_uk_not_found": price_not_found.get('amazon.co.uk', False),
    })

@app.get("/past_searches", response_class=HTMLResponse)
async def past_searches(request: Request):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_data")
    past_searches = cursor.fetchall()
    conn.close()

    # Convert the fetched data into a list of dictionaries
    past_searches_list = [{
        "timestamp": search[1],
        "query": search[2],
        "item_name": search[3],
        "com_price": search[4],
        "ca_price": search[5],
        "de_price": search[6],
        "co_uk_price": search[7]
    } for search in past_searches]

    return templates.TemplateResponse("past_searches.html", {"request": request, "past_searches": past_searches_list})
