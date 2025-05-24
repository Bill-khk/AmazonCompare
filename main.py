from selenium.common.exceptions import NoSuchElementException
from flask import Flask, render_template, url_for, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import time

dict_url = {
    'France': "https://www.amazon.fr/",
    'Germany': "https://www.amazon.de/",
    'Belgium': "https://www.amazon.com.be/",
}

app = Flask(__name__)


@app.route("/")
def hello():
    return render_template('home.html', dict_url=dict_url)


@app.route("/search/")
def search():
    global dict_url
    comparative_list = []
    item = request.args.get('item')
    # france = request.args.get('France')

    print(f'Item:{item}')
    if request.args.get('France'):
        result = search_online(item, dict_url['France'])
        comparative_list.append(result)
    if request.args.get('Germany'):
        result = search_online(item, dict_url['Germany'])
        comparative_list.append(result)
    if request.args.get('Belgium'):
        result = search_online(item, dict_url['Belgium'])
        comparative_list.append(result)

    print(comparative_list)

    return render_template('home.html', dict_url=dict_url)


def search_online(item, URL):
    print(f'Looking in {URL}')
    ua = UserAgent()
    random_user_agent = ua.random  # Get a random user-agent

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument(f"user-agent={random_user_agent}")
    chrome_options.add_argument("--incognito")  # This prevents cookies from tracking repeated visits:
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 "
        "Safari/537.36")
    service = Service("C:/Program Files/Google/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Apply stealth mode
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    try:
        # Open Google
        driver.get(URL)
        # Disable navigator.webdriver detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        time.sleep(1)  # Allow time for JavaScript to load

        # Language
        try:
            target = driver.find_element(By.CLASS_NAME, 'redir-overlay')
            target = target.find_element(By.CLASS_NAME, 'redir-a-button-center') # TODO to correct
            target.click()
        except NoSuchElementException:
            pass

        # Cookies :
        try:
            target = driver.find_element(By.ID, 'a-autoid-0')
            target.click()
        except NoSuchElementException:
            pass

        try:
            target = driver.find_element(By.ID, 'twotabsearchtextbox')
            target.click()
        except NoSuchElementException:
            target = driver.find_element(By.ID, 'nav-bb-search')
            target.click()

        target.send_keys(item)
        target = driver.find_element(By.ID, 'nav-search-submit-button')
        target.click()

        result_list = driver.find_elements(By.CLASS_NAME, 'puis-card-container')
        final_result = []
        to_break = False
        for item_result in result_list:
            try:
                title_element = item_result.find_element(By.CSS_SELECTOR, 'h2')
                match = 0
                for word in item.split():
                    lower_word = word = word[0].lower() + word[1:]
                    # print(f'{word.capitalize()} or {lower_word} in {title_element.text}')  # Used as a test
                    if title_element.text.find(word.capitalize()) > 0:
                        match += 1
                    elif title_element.text.find(lower_word) > 0:  # Manage capitalize words
                        match += 1

                match = match / len(item.split())
                # print(f'Final match: {match} for {title_element.text}')  # Used to test
                # TODO threshold based on number of word
                if match > 0.8:  # Base the result on the % of correspondence between item name and result title
                    final_result.append(title_element.text)
                    final_result.append(item_result.find_element(By.CLASS_NAME, 'a-price-whole').text)
                    final_result.append(item_result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href'))
                    to_break = True
            except NoSuchElementException:
                print(f"No <h2> found in {item}.")

            if to_break:
                break

        print(f'Final item selection: {final_result}')
        return final_result

    finally:
        # Close the browser
        #driver.quit()
        pass


if __name__ == "__main__":
    app.run()
