from ui import ScraperUI
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from datetime import datetime
from bs4 import BeautifulSoup
from tinydb import TinyDB
import tkinter as tk
import logging
import requests
import logging
import time

def main():
    logging.basicConfig(filename='./data/ErrorLog.log', level=logging.ERROR)
    db = TinyDB('db.json')
    listings_table = db.table('seen_listings')
    links_table = db.table('links')
    discord_table = db.table('discord')
    root = tk.Tk()
    app = ScraperUI(master=root)
    scraper_callable = lambda *args: scrape_and_send(app=app, discord_table=discord_table, links_table=links_table, listings_table=listings_table)
    app.scraper_function = scraper_callable
    root.mainloop()

# Scraper logic
def scrape_and_send(app, discord_table, links_table, listings_table):
        while True:
            try:
                seen_listing_ids = {doc['listing'] for doc in listings_table.all()}
                app.write_to_info("Getting links . . .\n")
                links = links_table.all()
                for link in links:
                    app.write_to_info(f"Now scraping: \n{link['url']}")
                    cars = scrape_craigslist(app, link['url'])
                    app.write_to_info(
                        f"Finished scraping @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n"
                    )
                    if cars:
                        for car in cars:
                            listing_id = car['link'].split('/')[-1]
                            if listing_id not in seen_listing_ids:
                                app.write_to_info(
                                    f"\nNew listing found: {listing_id}, sending to discord.")
                                message = construct_payload(app, car)
                                send_discord_message(app, message, discord_table)
                                listings_table.insert({'listing': listing_id})
                                seen_listing_ids.add(listing_id)
                app.write_to_info(
                    f"\nNow waiting {app.sleep_time} minutes until next scrape . . .")
                time.sleep(app.sleep_time * 60)
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                app.write_to_info(f"An error occurred in the scraper thread: {e}")
                return

def scrape_craigslist(app, link):
    try:
        content = get_html_selenium(link)
        soup = BeautifulSoup(content, 'html.parser')
        cars = get_cars(soup)
        return cars
    except requests.exceptions.RequestException as e:
        app.write_to_info(f"Error during web request: {e}")
        return None
    except Exception as e:
        app.write_to_info(f"An error occurred: {e}")
        return None

def get_html_selenium(url):
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(2)
    html = driver.page_source
    driver.quit()
    return html

def get_cars(soup):
    cars = []
    for div in soup.find_all('div', {"class": "gallery-card"}):
        car = {}
        link = div.find('a').get('href').strip()
        car['link'] = link
        title = div.find('span', class_='label')
        if title:
            title = title.text.strip()
            car['title'] = title
        price = div.find('span', class_='priceinfo')
        if price:
            price = price.text.strip()
            car['price'] = price
        info = div.find('div', class_='meta')
        if info:
            info = info.text.strip()
            date = get_date(info)
            car['date'] = date
            odometer = get_odometer(date, info)
            car['odometer'] = f"{odometer} mi"
        cars.append(car)
    return cars

def get_date(info):
    date_str = info[:5]
    try:
        date = datetime.strptime(date_str, '%m/%d')
        return date.strftime('%m/%d')
    except ValueError:
        date = info[:4]
        return date

def get_odometer(date, info):
    info = info.replace(date, "").split()
    return info[0]

# Discord communication
def send_discord_message(app, message, discord_table):
    app.write_to_info(message)
    discord_settings = discord_table.all()
    if discord_settings:
        discord_data = discord_settings[0]
        channel_url = discord_data.get("channel_url")
        auth = discord_data.get("auth_token")
    payload = {"content": message}
    headers = {"Authorization": auth}
    response = requests.post(
        channel_url, json=payload, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to send Discord message: {response.text}")

def construct_payload(app, car):
    try:
        message = (
            f"Title: {car.get('title', 'Not Available')}\n"
            f"Odometer: {car.get('odometer', 'Not Available')}\n"
            f"Date: {car.get('date', 'Not Available')}\n"
            f"Price: {car.get('price', 'Not Available')}\n"
            f"Link: {car.get('link', 'Not Available')}"
        )
    except Exception as e:
        app.write_to_info(f"Error: {e}")
        message = None
    return message

if __name__ == "__main__":
    main()