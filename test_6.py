import google.generativeai as genai

with open('gemini_key.txt', 'r') as f:
    key = f.read().strip()
genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-exp-1206')
response = model.generate_content("Explain how AI works")
print(response.text)