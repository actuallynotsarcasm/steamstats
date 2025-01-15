import requests, certifi

proxies = {
    'http': 'http://44.219.175.186:80',
    'https': 'http://44.219.175.186:80',
}

#url = 'https://www.httpbin.org/get'
url = 'https://www.csgodatabase.com/skins/'

#resp = requests.get(url)
resp = requests.get(url, cert=certifi.where())
print(resp.status_code)

with open('proxy_test_resp.html', 'w', encoding='utf-16') as f:
    f.write(str(resp.text))

#print(certifi.contents())

with open('C:\\Users\\timof\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\certifi\\cacert.pem', 'r') as f:
    #print(f.read())
    pass