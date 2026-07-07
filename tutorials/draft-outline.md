# How to Scrape the Web (with Python)

## Intro to Python
- You're familiar with Excel/Sheets formulas. Think of Python like Excel formulas, but instead of just phrase-like length, it can be much longer and more powerful.
- A formula is the way we instruct the computer to do specific math. It's a way we talk to the computer. The syntax is a language, because it IS a language. Python is another programming language, but more comprehensive and run in a different environment. There are hundreds (if not thousands) of other languages that computers can understand and use to run what we ask them to do.
- Analogy:
  - Common excel formula = 1 sentence = roughly a Python statement or one-liner instruction
  - 1 paragraph = a Python function (a reusable block of instructions)
  - 1 page/document = 1 Python script
- A **Notebook** (like Jupyter) is a way to run Python block by block. Each cell in a notebook is typically run sequentially from top to bottom, making it very easy to test code step-by-step.
- Python can do almost anything a computer can do, not just scraping. It can train machine learning models, act as a web server, build games, automate tasks, etc.
- Now, we will use it for scraping
- In Python, there's something called a **package** or **library**. It's a collection of code (functions) written by other people, published for free, which we can download and use. Because of this, we don't have to build complex functionalities from scratch; we can leverage the open-source community's work.
- Popular Python libraries used for scraping:
  - **Requests**: To fetch the webpage from the internet (like typing a URL and hitting enter).
  - **BeautifulSoup**: To read and extract specific information from the HTML structure.
  - **Selenium / Playwright**: For more complex sites that require clicking buttons, scrolling, or loading JavaScript (browser automation).
  - **Pandas**: To structure the scraped data into a nice table and save it to an Excel or CSV file.

### What We Need to Run Python
- We need a Python Interpreter installed on our computer.
- OR use a cloud computer (like GitHub Codespaces).
- OR use a cloud notebook (like **Google Colab**), which is highly recommended for beginners because it requires zero setup and runs in your browser.

## Anatomy of a Web Page
- Open an example web page, right-click, and select "Inspect" (or View Page Source). You will see the underlying code structure. This is built using three core languages:
  - **HTML (HyperText Markup Language)**: The structure and content (text, links, images).
  - **CSS (Cascading Style Sheets)**: The styling (colors, layout, fonts).
  - **JavaScript (JS)**: The interactivity (animations, loading new data without refreshing).
- What we visually see in the browser is all of this code **rendered** in a way that's easy for humans to use and navigate.

## How Web Scraping Works
- A Python web scraper fetches this underlying code (usually HTML) and relies on its structure to extract the specific patterns and information we need.
- **Navigating pages:**
  - **Pagination (Sequential)**: Many websites have URL paths indexed sequentially (e.g., `page=1`, `page=2`). Python can easily loop through these increasing numbers to scrape multiple pages automatically.
  - **Crawling / Spidering**: If the URLs are not structured sequentially (e.g., using random IDs or blog titles), we first scrape the links from an initial page (like a home page or sitemap), store them in a list, and then have Python open that list of URLs one by one.
- **Extracting data (Parsing):**
  - On each page, Python "sees" the raw HTML behind the curtain, not the visual page. Using tools like BeautifulSoup, it navigates the HTML-CSS tags to pinpoint and extract *only* the specific text or data we're looking for, ignoring the rest.

## Ethical & Legal Considerations (Important!)
- **robots.txt**: Always check a website's `robots.txt` file (e.g., `website.com/robots.txt`) to see what is allowed to be scraped.
- **Rate Limiting**: Don't scrape too fast! Add delays (sleep) between your requests, otherwise, you might overwhelm their servers (like a mini-DDoS attack) and get your IP address banned.
- **Terms of Service**: Be mindful of private data, copyrights, and the website's terms of service.


