import os
import requests
from flask import Flask, flash, redirect, render_template, request, session
from flask_session.__init__ import Session
from tempfile import mkdtemp
import time

from helpers import crawl_required, crawl_urls
from url import Url

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Make sure API key is set
if not os.environ.get("CRUX_API_KEY"):
    raise RuntimeError("CRUX_API_KEY not set")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# List of all the hostname URLs to include
all_links = []
all_urls = []
urls_data = []


@app.after_request
def after_request(response):
    """Ensure responses are not cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    """Get user to crawl a website"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        domain = request.form.get("domain")

        # Ensure username was submitted
        if not request.form.get("domain"):
            print("missing domain")

        # Crawl the main page given for URLs of same domain
        try:
            crawl_urls(domain, domain, all_links, all_urls)
        except requests.exceptions.HTTPError:
            print("wrong url")

        # Crawl all URLs in the URL list to check for any new URLs from the same domain
        for link in all_links:
            try:
                crawl_urls(domain, link, all_links, all_urls)           
            except requests.exceptions.HTTPError:
                pass
        
        # Create URL objects to record CRUX data and append to URL data list
        for url in all_urls:
            # Delay the CRUX function depending on execution time
            start_time = time.time()
            url_data = Url(url)
            urls_data.append(url_data)
            end_time = time.time()
            if end_time - start_time < 0.4 and len(all_urls) > 150:
                time.sleep(0.4 - (end_time - start_time))

        for url in urls_data:
            print(url)

        # Remember which domain was crawled
        session["crawled"] = domain

        # Redirect user to home page
        return redirect("/stats")

    elif not session:
        return render_template("index.html")

    else:
        return redirect("/stats")


@app.route("/info")
def info():
    """Information about the application"""
    # Redirect user to crawl form
    return render_template("info.html")


@app.route("/new-crawl")
def new_crawl():
    """Remove crawled website"""
    # Forget any crawled website
    session.clear()
    all_links.clear()
    all_urls.clear()
    urls_data.clear()   

    # Redirect user to crawl form
    return redirect("/")


@app.route("/stats")
@crawl_required
def stats():
    """Page Speed Stats"""
    return render_template("stats.html", urls=urls_data)


if __name__=='__main__':
    app.run(debug=True)