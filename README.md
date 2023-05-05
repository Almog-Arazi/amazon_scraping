# a web scraping project that extracts product information from Amazon.com.

This script was developed during the course "From Idea to App using AI Tools," leveraging the ChatGPT AI language model.

four files for a web scraping project that extracts product information from Amazon.com. The files are:

**app.py:** This is the main file written in Python using the FastAPI framework. It contains the code for the web server, routes, and the functions to scrape Amazon products.

**search.html:** This is an HTML file that represents the search page of the application. It contains a form where users can input their search query to find products on Amazon.

**result.html:** This is an HTML file that represents the search result page of the application. It displays the top 10 products found on Amazon based on the user's search query.

**product.html:** This is an HTML file that represents the product details page of the application. It displays the product image, price in USD, and price in Euros (Amazon.de).

**database.py:** This Python file contains the code to create and connect to a SQLite database named "amazon_data.db".

**past_searches.html:** This HTML file represents the page where users can view their past search queries and the time of the search.
## The project works as follows:

The user visits the search page and enters a search query.
The server processes the search query and scrapes the top 10 products from Amazon.com.
The server displays the search results in a table, and the user can click on a button to view the product details.
The server then scrapes the product price in Euros (Amazon.de) and displays the product details, including the image, price in USD, and price in Euros.
To run the project, you should have Python and FastAPI installed. You can follow these

## steps to run the project:

#### Install the required packages:
bash
Copy code
pip install fastapi
pip install uvicorn
pip install requests
pip install beautifulsoup4
pip install selenium
pip install typing
pip install decimal

Save the app.py, search.html, result.html, and product.html files in a directory. Make sure to create subdirectories named static and templates. Save the .html files inside the templates directory.

## may attention -change to your path in app.py line 39
 **driver = webdriver.Chrome(executable_path='/Users/almog/chromedriver/chromedriver', options=chrome_options) 
**

In the terminal, navigate to the project directory and run the following command:

bash
Copy code
uvicorn app:app --reload
Open your web browser and visit http://127.0.0.1:8000/ to access the application.

or write  python -m uvicorn app:app --reload then open http://127.0.0.1:8000 

if you want to pass the alert of Daily searches cap, write  
#### resetCounter() in browser terminal.


**know it's slow, but it is my purpose to avoid Amazon's block.**

![](https://i.ibb.co/zbKvn4t/2023-05-05-223306.png)

![](https://i.ibb.co/DpHWRzJ/2023-05-05-223649.png)

##   enjoy :)

