from ui import ScraperUI
import tkinter as tk
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import requests
import logging
import time

def initialize():
    logging.basicConfig(filename='./data/ErrorLog.log', level=logging.ERROR)
    files_to_create = ['./links.txt', './discord.txt',
                       './data/seen_listings.txt']
    for file in files_to_create:
        try:
            with open(file, 'x') as _:
                pass
        except FileExistsError:
            pass

def main():
    initialize()
    root = tk.Tk()
    _ = ScraperUI(master=root, scraper_function=scrape_and_send)
    root.mainloop()

# Basic info 
def get_discord_login(file_path='./discord.txt'):
    try:
        with open(file_path, 'r') as file:
            channel_url = file.readline()
            auth = file.readline()
        return channel_url, auth
    except Exception as e:
        ScraperUI.write_to_info(f"\nError: {e}")
        return

def get_seen_listings(file_path='./data/seen_listings.txt'):
    try:
        with open(file_path, 'r') as file:
            seen_listings = file.read().splitlines()
        return seen_listings
    except FileNotFoundError:
        return []

def add_seen_listing(listing_id):
    with open('./data/seen_listings.txt', 'a') as file:
        file.write(f"{listing_id}\n")


# Scraper logic
def scrape_and_send():
        while True:
            try:
                seen_listings = get_seen_listings()
                ScraperUI.write_to_info("Getting links . . .\n")
                links = ScraperUI.get_links()
                for link in links:
                    ScraperUI.write_to_info(f"Now scraping: \n{link}")
                    cars = scrape_craigslist(link)
                    ScraperUI.write_to_info(
                        f"Finished scraping @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n"
                    )
                    for car in cars:
                        listing_id = car['link'].split('/')[-1]
                        if listing_id not in seen_listings:
                            ScraperUI.write_to_info(
                                f"\nNew listing found: {listing_id}, sending to discord.")
                            message = construct_payload(car)
                            send_discord_message(message)
                            add_seen_listing(listing_id)
                ScraperUI.write_to_info(
                    f"\nNow waiting {ScraperUI.sleep_time} minutes until next scrape . . .")
                time.sleep(ScraperUI.sleep_time * 60)
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                return

def scrape_craigslist(link):
    try:
        content = get_html_selenium(link)
        soup = BeautifulSoup(content, 'html.parser')
        cars = get_cars(soup)
        return cars
    except requests.exceptions.RequestException as e:
        ScraperUI.write_to_info(f"Error during web request: {e}")
        return None
    except Exception as e:
        ScraperUI.write_to_info(f"An error occurred: {e}")
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
def send_discord_message(message):
    ScraperUI.write_to_info(message)
    channel_url, auth = get_discord_login()
    payload = {"content": message}
    headers = {"Authorization": auth}
    response = requests.post(
        channel_url, json=payload, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to send Discord message: {response.text}")

def construct_payload(car):
    try:
        message = (
            f"Title: {car.get('title', 'Not Available')}\n"
            f"Odometer: {car.get('odometer', 'Not Available')}\n"
            f"Date: {car.get('date', 'Not Available')}\n"
            f"Price: {car.get('price', 'Not Available')}\n"
            f"Link: {car.get('link', 'Not Available')}"
        )
    except Exception as e:
        ScraperUI.write_to_info(f"Error: {e}")
        message = None
    return message


if __name__ == "__main__":
    main()
