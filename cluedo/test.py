from google import genai
import json

key = json.load(open("keys.json", "r"))["gemini"]


client = genai.Client(api_key=key)


for model in client.models.list():
    print(model.name)