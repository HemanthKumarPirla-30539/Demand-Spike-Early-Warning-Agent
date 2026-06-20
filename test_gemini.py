import google.generativeai as genai

API_KEY = "AQ.Ab8RN6KbLQpx1bJm23njybHaOaz3_B77RYRBQHuSQgS8oMa1Ew"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Hello")

print(response.text)