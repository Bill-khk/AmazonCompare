from flask import Flask, render_template, url_for

dict_url = {
    'France': "https://www.amazon.fr/",
    'Germany': "https://www.amazon.de/",
    'Belgium': "https://www.amazon.com.be/",
}

app = Flask(__name__)


@app.route("/")
def hello():
    return render_template('home.html', dict_url=dict_url)

@app.route("/search/<item>&<code>")
def search(item, code):
    print(f'item: {item}')
    print(f'code: {code}')
    return render_template('home.html')


if __name__ == "__main__":
    app.run()
