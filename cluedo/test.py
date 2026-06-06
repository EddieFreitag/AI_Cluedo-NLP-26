from google import genai
import json

key = json.load(open("cluedo/keys.json", "r"))["gemini"]


client = genai.Client(api_key=key)


chat = client.chats.create(model="gemini-3.5-flash")

response1 = chat.send_message("I have 2 dogs in my house.")
print("Response 1:", response1.text)

response2 = chat.send_message("How many paws are in my house?")
print("Response 2:", response2.text)

