# Llm-News

## Setup
1. Create a venv - `python3 -m venv venv`
2. Activate the venv - `source venv/bin/activate`
3. Install the requirements - `pip install -r requirements.txt`
4. Copy .example.env to .env
5. Create OpenAI key and add to .env from https://platform.openai.com/api-keys
6. Create Google API key and add to .env from https://console.cloud.google.com/apis/credentials
7. Create search engine and add searchengine-ID to .env from https://programmablesearchengine.google.com/controlpanel/all
8. Run the app - `uvicorn main:app --reload`

## Google api
The google api allows us to search using google without the need to create an comprehensive crawler. In comparison to Hackernews the google api allows us to search on any terms, websites, etc. Keep in mind that a well-defined search string/filter is needed to reduce noise to a minimum.

### Creating search engines
Step 7 in the setup mentions the searchengine-ID. This id is a reference to the 'Programmable searchengine' from google. The programmable searchengine defines the websites that needs to be searched. It is advised to use only one endpoint from a websites per search engine, for example, https://website.com/en/articles/artificial-intelligence/*. This is necessary, because the google api only allows us to retrieve a maximum of 100 results per search engine.

### Testing search engines
It is advised to test if the search query does not obtain more than 100 results weekly and does also not contain too much noise. Use the parameters from the function 'fetch_news_page' in 'google_api_service.py' and the search engine id to test the search engine. You can test the search engine on the following page: https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list?apix=true

## Operating system
For the google api services to work this api needs to run on the windows operating system. This is necessary for the undetected-chromedriver to run on certain websites, because we use GUI to bypass any bot detection. On Ubuntu or Docker it might be possible to use xvfb to scrape, but this is not tested and the code structure of google_api_service.py should be changed accordingly.