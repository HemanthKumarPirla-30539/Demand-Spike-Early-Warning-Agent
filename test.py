import google.generativeai as genai

API_KEY = "AQ.Ab8RN6J7CX4Pbtc5i8l475Q-b5o_41otZzPgpBWt6W8oMkNa1g"

genai.configure(api_key=API_KEY)

for m in genai.list_models():
    print(m.name)