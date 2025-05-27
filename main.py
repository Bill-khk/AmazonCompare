from selenium.common.exceptions import NoSuchElementException
from flask import Flask, render_template, url_for, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from selenium.webdriver.common.keys import Keys
import time

dict_url = {
    'France': "https://www.amazon.fr/",
    'Germany': "https://www.amazon.de/",
    'Belgium': "https://www.amazon.com.be/",
}

app = Flask(__name__)

# TODO put a slide to select the wanted match between research and returned item
# TODO put a suggestion when typing in the research bar ?

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

    return render_template('home.html', dict_url=dict_url, list=comparative_list)


def test_word(word):
    lower = word[0].lower() + word[1:]
    return word.capitalize(), lower


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

    # Open Google
    driver.get(URL)
    # Disable navigator.webdriver detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    time.sleep(1)  # Allow time for JavaScript to load

    # Language
    try:
        target = driver.find_element(By.CLASS_NAME, 'redir-a-button-desktop')
        target.click()
    except NoSuchElementException:
        pass

    # Cookies :
    try:
        target = driver.find_element(By.ID, 'a-autoid-0')
        target.click()
    except NoSuchElementException:
        pass

    # Search bar
    try:
        target = driver.find_element(By.ID, 'twotabsearchtextbox')
        target.click()
    except NoSuchElementException:
        target = driver.find_element(By.ID, 'nav-bb-search')  #Changed by class
        target.click()

    target.send_keys(item)
    target.send_keys(Keys.ENTER)
    time.sleep(0.5)

    result_list = driver.find_elements(By.CLASS_NAME, 'puis-card-container')
    final_result = []
    temp_candidate = []  # Use to store item while looking for the other match
    max_candidate = 3
    candidate_number = 0
    for item_result in result_list:
        if not candidate_number == max_candidate:  # Used to limit the number or search returned
            temp_item = []
            next_item = False  # Use to validate candidate based on first few word of returned item
            try:
                title_element = item_result.find_element(By.CSS_SELECTOR, 'h2')
                match = 0

                # The word in search must be one of the three first words
                test_title = title_element.text.lower().split()[0:3]
                print('-------------------------------')
                test = 0
                for word in item.lower().split():
                    if word in test_title:
                        test += 1
                        print(f'{word} found in {test_title}')

                print(f'Test result: {test} for {test_title}')
                if test == 0:
                    next_item = True

                if not next_item:
                    print('Candidate --')
                    candidate_number += 1
                    # Check the % of words in the research compare to in the title
                    # TODO put all the item.split in lowercase - to manage scenario like AirPod
                    for word in item.lower().split():
                        # lower_word = word[0].lower() + word[1:]
                        print(f'{word} in {title_element.text.lower()}')  # Used as a test
                        if word in title_element.text.lower():
                            match += 1

                    match = match / len(item.split())
                    print(f'Final match: {match} for {title_element.text}')  # Used to test
                    # TODO threshold based on number of word
                    if match > 0.6:  # Base the result on the % of correspondence between item name and result title
                        print("It's a match !")
                        final_result.append(title_element.text)
                        final_result.append(item_result.find_element(By.CLASS_NAME, 'a-price-whole').text)
                        final_result.append(item_result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href'))
                        final_result.append(item_result.find_element(By.CLASS_NAME, 's-image').get_attribute('src'))

                        # Temporary storage
                        temp_item.append(title_element.text)
                        temp_item.append(item_result.find_element(By.CLASS_NAME, 'a-price-whole').text)
                        temp_item.append(item_result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href'))
                        temp_item.append(item_result.find_element(By.CLASS_NAME, 's-image').get_attribute('src'))
                        temp_candidate.append(temp_item)

            except NoSuchElementException:
                print(f"No <h2> found in {item}.")

    # Analysing temp candidate
    print(temp_candidate)
    mean_price = 0
    for item in temp_candidate:
        mean_price += int(item[1])
    mean_price = mean_price / len(temp_candidate)

    # Keep item if the price is around the mean price of all candidate
    temp_candidate_bis = [item for item in temp_candidate if
                          (mean_price + mean_price * 0.3) > int(item[1]) > (mean_price - mean_price * 0.3)]

    print(temp_candidate_bis)
    print(f'Final item selection: {final_result}')
    # Close the browser
    driver.close()
    return final_result


if __name__ == "__main__":
    app.run()
