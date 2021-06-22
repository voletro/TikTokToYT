"""
████████╗██╗██╗  ██╗████████╗ ██████╗ ██╗  ██╗     ████████╗ ██████╗     ██╗   ██╗████████╗
╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔═══██╗██║ ██╔╝     ╚══██╔══╝██╔═══██╗    ╚██╗ ██╔╝╚══██╔══╝
   ██║   ██║█████╔╝    ██║   ██║   ██║█████╔╝         ██║   ██║   ██║     ╚████╔╝    ██║   
   ██║   ██║██╔═██╗    ██║   ██║   ██║██╔═██╗         ██║   ██║   ██║      ╚██╔╝     ██║   
   ██║   ██║██║  ██╗   ██║   ╚██████╔╝██║  ██╗        ██║   ╚██████╔╝       ██║      ██║   
   ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝        ╚═╝    ╚═════╝        ╚═╝      ╚═╝   

By jakenic

Downloads a trending TikTok video and uploads it to YouTube. This will happen every half an hour (30 mins).

Requirements:
Firefox - https://www.mozilla.org/en-US/firefox/new/
GeckoDriver - https://github.com/mozilla/geckodriver/releases

Setup:
1. Extract downloaded zip file to a folder. Go to that folder in a terminal.
2. Run "pip install -r requirements.txt" inside the downloaded folder.
3. Sign into YouTube on Firefox with the account you want to upload the videos to.
4. Install the EditThisCookie extension on Firefox, open it, and click the export button to export login cookies to clipboard.
5. Open the file called login.json in a text editor. Paste the exported login cookies into the file and save.
6. Run the main.py script!

Special thanks to these people for making this project possible:
davidteather - TikTokApi - https://github.com/davidteather/TikTok-Api
SeleniumHQ - selenium - https://github.com/SeleniumHQ/selenium
"""


import urllib.request
import os
import logging
from typing import Dict, List
import logging
import re
from datetime import datetime
from time import sleep
import json
from TikTokApi import TikTokApi
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

currentpath = os.getcwd()

def domain_to_url(domain: str) -> str:
    if domain.startswith("."):
        domain = "www" + domain
    return "http://" + domain


def login_using_cookie_file(driver: WebDriver, cookie_file: str):
    """Restore auth cookies from a file. Does not guarantee that the user is logged in afterwards.
    Visits the domains specified in the cookies to set them, the previous page is not restored."""
    domain_cookies: Dict[str, List[object]] = {}
    with open(cookie_file) as file:
        cookies: List = json.load(file)
        # Sort cookies by domain, because we need to visit to domain to add cookies
        for cookie in cookies:
            try:
                domain_cookies[cookie["domain"]].append(cookie)
            except KeyError:
                domain_cookies[cookie["domain"]] = [cookie]

    for domain, cookies in domain_cookies.items():
        driver.get(domain_to_url(domain + "/robots.txt"))
        for cookie in cookies:
            cookie.pop("sameSite", None)  # Attribute should be available in Selenium >4
            cookie.pop("storeId", None)  # Firefox container attribute
            try:
                driver.add_cookie(cookie)
            except:
                print(f"Couldn't set cookie {cookie['name']} for {domain}")


def confirm_logged_in(driver: WebDriver) -> bool:
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "avatar-btn")))
        return True
    except TimeoutError:
        return False
def upload_file(
        driver: WebDriver,
        video_path: str,
        title: str,
        description: str,
        thumbnail_path: str = None,
):
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ytcp-button#create-icon"))).click()
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//tp-yt-paper-item[@test-id="upload-beta"]'))
    ).click()
    video_input = driver.find_element_by_xpath('//input[@type="file"]')
    video_input.send_keys(video_path)

    _set_basic_settings(driver, title, description, thumbnail_path)
    # Go to visibility settings
    for i in range(3):
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "next-button"))).click()

    _set_time(driver)
    _wait_for_processing(driver)
    # Go back to endcard settings
    driver.find_element_by_css_selector("#step-badge-1").click()
    #_set_endcard(driver)

    for _ in range(2):
        # Sometimes, the button is clickable but clicking it raises an error, so we add a "safety-sleep" here
        sleep(5)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "next-button"))).click()

    sleep(5)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "done-button"))).click()

    # Wait for the dialog to disappear
    sleep(5)
    logging.info("Upload is complete")
    driver.quit()


def _wait_for_processing(driver):
    # Wait for processing to complete
    progress_label: WebElement = driver.find_element_by_css_selector("span.progress-label")
    pattern = re.compile(r"(finished processing)|(processing hd.*)|(check.*)")
    current_progress = progress_label.get_attribute("textContent")
    last_progress = None
    while not pattern.match(current_progress.lower()):
        if last_progress != current_progress:
            logging.info(f'Current progress: {current_progress}')
        last_progress = current_progress
        sleep(5)
        current_progress = progress_label.get_attribute("textContent")


def _set_basic_settings(driver: WebDriver, title: str, description: str, thumbnail_path: str = None):
    title_input: WebElement = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                '//ytcp-mention-textbox[@label="Title"]//div[@id="textbox"]',

            )
        )
    )

    # Input meta data (title, description, etc ... )
    description_input: WebElement = driver.find_element_by_xpath(
        '//ytcp-mention-textbox[@label="Description"]//div[@id="textbox"]'
    )
    thumbnail_input: WebElement = driver.find_element_by_css_selector(
        "input#file-loader"
    )

    title_input.clear()
    title_input.send_keys(title)
    description_input.send_keys(description)
    if thumbnail_path:
        thumbnail_input.send_keys(thumbnail_path)
    driver.find_element_by_css_selector("#toggle-button").click()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.NAME, "NOT_MADE_FOR_KIDS")
    )).click()


def _set_endcard(driver: WebDriver):
    # Add endscreen
    driver.find_element_by_css_selector("#endscreens-button").click()
    sleep(5)

    # Select endcard type from last video or first suggestion if no prev. video
    driver.find_element_by_css_selector("div.card:nth-child(1)").click()

    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "save-button"))).click()


def _set_time(driver: WebDriver):
    # Start time scheduling
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, "PUBLIC"))).click()

def main():
    title = """
████████╗██╗██╗  ██╗████████╗ ██████╗ ██╗  ██╗     ████████╗ ██████╗     ██╗   ██╗████████╗
╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔═══██╗██║ ██╔╝     ╚══██╔══╝██╔═══██╗    ╚██╗ ██╔╝╚══██╔══╝
   ██║   ██║█████╔╝    ██║   ██║   ██║█████╔╝         ██║   ██║   ██║     ╚████╔╝    ██║   
   ██║   ██║██╔═██╗    ██║   ██║   ██║██╔═██╗         ██║   ██║   ██║      ╚██╔╝     ██║   
   ██║   ██║██║  ██╗   ██║   ╚██████╔╝██║  ██╗        ██║   ╚██████╔╝       ██║      ██║   
   ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝        ╚═╝    ╚═════╝        ╚═╝      ╚═╝   
    """
    print(title)
    api = TikTokApi.get_instance()
    trending = api.trending(count=1, custom_verifyFp="")
    for tiktok in trending:
        tvideo = tiktok['video']
        link = tvideo['downloadAddr']
        author = tiktok['author']
        username = author['uniqueId']
        id = tiktok['id']
        desc = tiktok['desc']
        print("Downloading video...")
        urllib.request.urlretrieve(link, f'{username}-{id}.mp4')
    title = f"{desc} - @{username} - For You"
    description = f"Credit to the original creator, @{username}. Check out their other content here: https://tiktok.com/@{username}"
    print("Downloaded video!")
    print(title)
    print("Starting upload...")

    logging.getLogger().setLevel(logging.INFO)



    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("intl.accept_languages", "en-us")
    firefox_profile.update_preferences()
    driver = webdriver.Firefox(firefox_profile)

    #driver = webdriver.Chrome()

    driver.set_window_size(1920, 1080)
    login_using_cookie_file(driver, cookie_file='login.json')
    driver.get("https://www.youtube.com")

    assert "YouTube" in driver.title

    try:
        confirm_logged_in(driver)
        driver.get("https://studio.youtube.com")
        assert "Channel dashboard" in driver.title
        driver.file_detector = LocalFileDetector()
        upload_file(
            driver,
            video_path=currentpath + f'\{username}-{id}.mp4',
            title=title,
            description=description,
        )
    except:
        driver.close()
        raise
    
while True:
    os.system('cls' if os.name in ('nt', 'dos') else 'clear')
    main()
    print("Finished upload.")
    print("Waiting for next upload.")
    sleep(1800)