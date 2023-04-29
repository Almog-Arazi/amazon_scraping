# a web scraping project that extracts product information from Amazon.com.

This script was developed during the course "From Idea to App using AI Tools," leveraging the ChatGPT AI language model.

four files for a web scraping project that extracts product information from Amazon.com. The files are:

**app.py:** This is the main file written in Python using the FastAPI framework. It contains the code for the web server, routes, and the functions to scrape Amazon products.

**search.html:** This is an HTML file that represents the search page of the application. It contains a form where users can input their search query to find products on Amazon.

**result.html:** This is an HTML file that represents the search result page of the application. It displays the top 10 products found on Amazon based on the user's search query.

**product.html:** This is an HTML file that represents the product details page of the application. It displays the product image, price in USD, and price in Euros (Amazon.de).

## The project works as follows:

The user visits the search page and enters a search query.
The server processes the search query and scrapes the top 10 products from Amazon.com.
The server displays the search results in a table, and the user can click on a button to view the product details.
The server then scrapes the product price in Euros (Amazon.de) and displays the product details, including the image, price in USD, and price in Euros.
To run the project, you should have Python and FastAPI installed. You can follow these steps to run the project:

Install the required packages:
bash
Copy code
pip install fastapi
pip install uvicorn
pip install requests
pip install beautifulsoup4
Save the app.py, search.html, result.html, and product.html files in a directory. Make sure to create subdirectories named static and templates. Save the .html files inside the templates directory.

In the terminal, navigate to the project directory and run the following command:

bash
Copy code
uvicorn app:app --reload
Open your web browser and visit http://127.0.0.1:8000/ to access the application.