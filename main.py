import mechanize
import json
import time
import os
import urllib.parse
from flask import Flask, request, render_template
from threading import Thread

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Get data from the form
        appstate_files = request.files.getlist('appstate_files')  # Changed to use request.files
        num_posts = int(request.form['num_posts'])
        urls = request.form.getlist('urls')
        time_interval = int(request.form['time_interval'])

        # Validate the inputs
        if not appstate_files or num_posts <= 0 or time_interval <= 0:
            return "Invalid input data", 400

        # Save uploaded files temporarily
        file_paths = []
        for file in appstate_files:
            file_path = os.path.join('/tmp', file.filename)  # Temporary directory for files
            file.save(file_path)
            file_paths.append(file_path)

        # Start the main process in a separate thread
        Thread(target=main, args=(file_paths, num_posts, urls, time_interval)).start()
        return "Process started. Check the console for updates."
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error in submit: {str(e)}")
        return "Internal Server Error", 500

def load_cookies_from_files(appstate_files, browsers):
    for file_path, browser in zip(appstate_files, browsers):
        cookies = mechanize.CookieJar()
        try:
            with open(file_path, 'r') as f:
                cookies_data = json.load(f)
                for key, value in cookies_data.items():
                    c = mechanize.Cookie(
                        version=0, name=key, value=value,
                        port=None, port_specified=False,
                        domain='facebook.com', domain_specified=True, domain_initial_dot=False,
                        path='/', path_specified=True,
                        secure=False, expires=None,
                        discard=True, comment=None, comment_url=None, rest={}
                    )
                    cookies.set_cookie(c)
            browser.set_cookiejar(cookies)
        except OSError as e:
            print(f"Error opening {file_path}: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")

def extract_profile_ids(cookies):
    return [cookie.value for cookie in cookies if cookie.name == 'c_user']

def open_and_submit_post(browser, url, comment_text):
    try:
        browser.set_handle_robots(False)
        browser.set_handle_refresh(False)
        g_headers = {
            'authority': 'mbasic.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'referer': 'www.google.com',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101"',
            'sec-ch-ua-full-version-list': '" Not A;Brand";v="99.0.0.0", "Chromium";v="101.0.4951.40"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua-platform-version': '"11.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
        }
        browser.addheaders = list(g_headers.items())
        response = browser.open(url)
        browser.select_form(nr=0)

        # Set the comment text
        browser.form.find_control(name='comment').value = comment_text
        browser.submit(name='post')
        
        print(f"Successfully Commented ✔ =>\n{comment_text}")
    except Exception as e:
        print(f"Error occurred while opening and submitting 'post' on {url}: {str(e)}")

def main(appstate_files, num_posts, urls, time_interval):
    try:
        browsers = [mechanize.Browser() for _ in range(len(appstate_files))]
        load_cookies_from_files(appstate_files, browsers=browsers)

        for i, browser in enumerate(browsers):
            profile_ids = extract_profile_ids(browser.cookiejar)
            print(f"Profile IDs {i + 1}: {profile_ids}")

        while True:
            for browser, profile_ids in zip(browsers, [extract_profile_ids(browser.cookiejar) for browser in browsers]):
                for profile_id in profile_ids:
                    print(f"\n[➢] Using Profile ID: {profile_id}")

                    for j, url in enumerate(urls):
                        print(f"\n[+] Opening and submitting 'post' with Profile ID: {profile_id} | URL {j + 1}")
                        try:
                            open_and_submit_post(browser, url)
                        except Exception as e:
                            print(f"Error occurred while opening and submitting 'post' on {url}: {str(e)}")
                        time.sleep(time_interval)

    except Exception as e:
        print(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
