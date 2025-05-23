from flask import Flask, render_template, url_for, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import time
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from selenium.webdriver.common.by import By


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
    item = request.args.get('item')
    france = request.args.get('France')
    print(f'Item:{item}')
    if france:
        print(f'Looking in France-{dict_url['France']}')
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
            driver.get(dict_url['France'])
            # Disable navigator.webdriver detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            time.sleep(2)  # Allow time for JavaScript to load

            # Cookies :
            target = driver.find_element(By.ID, 'a-autoid-0')
            target.click()
            target = driver.find_element(By.ID, 'twotabsearchtextbox')
            target.click()
            target.send_keys(item)
            target = driver.find_element(By.ID, 'nav-search-submit-button')
            target.click()





        finally:
            # Close the browser
            #driver.quit()
            pass

    return render_template('home.html', dict_url=dict_url)


if __name__ == "__main__":
    app.run()
