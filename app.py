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
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "search")))
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
            break

    amazon_domains = ['amazon.ca', 'amazon.de', 'amazon.co.uk']
    product_urls = {}

    for domain in amazon_domains:
        product_url = get_product_url(asin, domain)
        product_urls[domain] = product_url
        print(f'{domain}: {product_url}')  # Print the product URL to console

    return templates.TemplateResponse("product.html", {"request": request, "product_name": product_name, "img_url": img_url, "price": price, "asin": asin})
