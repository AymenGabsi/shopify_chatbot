from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_NAME = os.getenv("SHOPIFY_STORE_NAME")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    # Optional: Replace with dynamic Shopify data
    #context = "This is a fashion store. We sell cotton t-shirts, jeans, and jackets."

    #Dynamic Context Using Shopify Dev Application
    shopify_token = SHOPIFY_ACCESS_TOKEN
    shop = SHOPIFY_STORE_NAME

    # res = requests.get(
    #     f"https://{shop}/admin/api/2024-04/products.json",
    #     headers={"X-Shopify-Access-Token": shopify_token}
    # )

    #Disabling Certificate While Calling The API
    res = requests.get(
        "https://gabsistore.myshopify.com/admin/api/2024-04/products.json",
        headers={"X-Shopify-Access-Token": shopify_token},
        verify=False  # 👈 disables SSL verification
    )

    products = res.json()['products']

    context = "\n".join([f"{p['title']}: {p['body_html']}" for p in products[:3]])

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful product assistant for a fashion store."},
            {"role": "user", "content": f"Context: {context}\n\n{user_message}"}
        ]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
