import requests

with open('gemini_key.txt', 'r') as f:
    key = f.read().strip()
model_name = 'gemini-exp-1206'
url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}'
req_data = {
    'contents': [
        {
            'parts': [
                {
                    'text': 'Explain how AI works'
                }
            ]
        }
    ]
}
headers = {
    'Content-Type': 'application/json'
}
with open('proxy.txt', 'r') as f:
    proxy_url = f.read()
proxies = {
    'http': proxy_url,
    'https': proxy_url
}
resp = requests.post(url, json=req_data, proxies=proxies)
print(resp.status_code)
print(resp.json()['candidates'][0]['content']['parts'][0]['text'])