import requests
from bs4 import BeautifulSoup as bs
import requests.cookies

username = 'test_name_for_x'
password = 'test_password_for_x'

url_login_page = 'https://x.com/i/flow/login?mx=2'
headers_login_page = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 OPR/115.0.0.0 (Edition Yx 05)'
}
resp_login_page = requests.get(url_login_page, headers=headers_login_page)
print('login_page:', resp_login_page.status_code)
soup_login_page = bs(resp_login_page.text, features='html.parser')
script_main_js = soup_login_page.select('script[src*=main]')
url_main_js = script_main_js[0].attrs['src']
resp_main_js = requests.get(url_main_js)
print('main_js:', resp_main_js.status_code)
main_js_text = resp_main_js.text
token_start_ind = main_js_text.find('"Bearer ') + 1
token_end_ind = main_js_text.find('"', token_start_ind)
auth_token = main_js_text[token_start_ind:token_end_ind]
print(auth_token)
script_cookie_data = list(filter(lambda x: 'document.cookie' in x.text, soup_login_page.find_all('script')))[0]
print(script_cookie_data)
cookies_init = resp_login_page.cookies
cookie_gt = requests.cookies.cookiejar_from_dict({

})
for c in resp_login_page.cookies:
    print(type(c))
    print(c.expires)
    break
#print(resp_login_page.cookies)
url = 'https://api.x.com/1.1/onboarding/task.json?flow_name=login'
init_data = {
    "input_flow_data": {
        "flow_context": {
            "debug_overrides": {},
            "start_location": {
                "location": "splash_screen"
                }
            }
        },
    "subtask_versions": {
        "action_list": 2,
        "alert_dialog": 1,
        "app_download_cta": 1,
        "check_logged_in_account": 1,
        "choice_selection": 3,
        "contacts_live_sync_permission_prompt": 0,
        "cta": 7,
        "email_verification": 2,
        "end_flow": 1,
        "enter_date": 1,
        "enter_email": 2,
        "enter_password": 5,
        "enter_phone": 2,
        "enter_recaptcha": 1,
        "enter_text": 5,
        "enter_username": 2,
        "generic_urt": 3,
        "in_app_notification": 1,
        "interest_picker": 3,
        "js_instrumentation": 1,
        "menu_dialog":1,
        "notifications_permission_prompt":2,
        "open_account": 2,
        "open_home_timeline": 1,
        "open_link": 1,
        "phone_verification": 4,
        "privacy_options": 1,
        "security_key": 3,
        "select_avatar": 4,
        "select_banner": 2,
        "settings_list": 7,
        "show_code": 1,
        "sign_up": 2,
        "sign_up_review": 4,
        "tweet_selection_urt": 1,
        "update_users": 1,
        "upload_media": 1,
        "user_recommendations_list": 4,
        "user_recommendations_urt": 1,
        "wait_spinner": 3,
        "web_modal": 1
    }
}
headers_init = {
    'Authorization': auth_token
}
resp_init = requests.post(url, json=init_data)
print(resp_init.status_code)
with open('resp_x.html', 'w') as f:
    f.write(resp_init.text)