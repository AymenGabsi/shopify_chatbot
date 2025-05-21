# Shopify WhatsApp AI Chatbot - Flask App (Deployable)

from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOP = "gabsistore.myshopify.com"
META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "Shopify WhatsApp AI Chatbot is running."

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification token mismatch", 403

    if request.method == 'POST':
        data = request.json
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            message = entry['messages'][0]
            phone_number = message['from']
            text = message['text']['body']

            reply = handle_message(text)
            send_whatsapp_message(phone_number, reply)

        return 'OK', 200


def send_whatsapp_message(phone, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)


def call_llama(messages):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={"model": "llama3-8b-8192", "messages": messages}
    )
    return response.json()["choices"][0]["message"]["content"]


def classify_intent_and_entities(user_message):
    prompt = f"""
Given this customer message, identify the intent and extract any relevant entities.

Format:
intent: one of [product_info, order_status, delivery_policy, return_policy, generic]
product_name: <if applicable>
order_id: <if applicable>
email: <if applicable>
info: <if applicable>

Message: "{user_message}"
"""
    messages = [
        {"role": "system", "content": "You extract intent and relevant data from customer messages."},
        {"role": "user", "content": prompt}
    ]
    content = call_llama(messages)
    result = {"intent": "generic", "product_name": None, "order_id": None, "email": None, "info": None}
    for line in content.splitlines():
        if line.startswith("intent:"): result["intent"] = line.split(":", 1)[1].strip()
        if line.startswith("product_name:"): result["product_name"] = line.split(":", 1)[1].strip()
        if line.startswith("order_id:"): result["order_id"] = line.split(":", 1)[1].strip()
        if line.startswith("email:"): result["email"] = line.split(":", 1)[1].strip()
        if line.startswith("info:"): result["info"] = line.split(":", 1)[1].strip()
    return result


def get_product_details(product_name):
    url = f"https://{SHOP}/admin/api/2024-04/products.json?title={product_name}"
    res = requests.get(url, headers={"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}, verify=False)
    data = res.json()
    return data['products'][0] if data['products'] else None


def extract_requested_info(product, info_type):
    if not product['variants']:
        return "No variant data available."

    title = product.get('title', 'N/A')
    description = product.get('body_html', 'N/A')
    prices = set(v['price'] for v in product['variants'])
    colors = set(v['option1'] for v in product['variants'] if 'option1' in v)
    sizes = set(v['option2'] for v in product['variants'] if 'option2' in v and v['option2'])
    total_inventory = sum(v.get('inventory_quantity', 0) for v in product['variants'])

    info_block = f"""
- Title: {title}
- Description: {description}
- Price(s): {', '.join(f'${p}' for p in prices)}
- Available colors: {', '.join(colors) if colors else 'N/A'}
- Sizes: {', '.join(sizes) if sizes else 'N/A'}
- Total stock: {total_inventory} units
"""

    return info_block


def get_order_info(order_id=None, email=None):
    if order_id:
        url = f"https://{SHOP}/admin/api/2024-04/orders.json?name={order_id}"
    elif email:
        url = f"https://{SHOP}/admin/api/2024-04/orders.json?email={email}"
    else:
        return None
    res = requests.get(url, headers={"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}, verify=False)
    orders = res.json().get('orders', [])
    return orders[0] if orders else None


def generate_llama_response(user_message, extracted_info):
    messages = [
        {"role": "system", "content": "You are a Shopify product assistant. ONLY use the information provided below. Do not guess. If the answer is not present in the product data, say 'I couldn't find that information.'"},
        {"role": "user", "content": f"""
PRODUCT DATA:
{extracted_info}

CUSTOMER QUESTION:
{user_message}

ANSWER:"""}
    ]
    return call_llama(messages)


def generate_generic_response(user_message):
    return call_llama([
        {"role": "system", "content": "You are a helpful assistant for a fashion store."},
        {"role": "user", "content": user_message}
    ])


def handle_message(user_text):
    analysis = classify_intent_and_entities(user_text)
    intent = analysis["intent"]

    if intent == "product_info" and analysis["product_name"]:
        product = get_product_details(analysis["product_name"])
        if product:
            info = extract_requested_info(product, analysis.get("info", "price"))
            return generate_llama_response(user_text, info)

    elif intent == "order_status" and (analysis["order_id"] or analysis["email"]):
        order = get_order_info(order_id=analysis["order_id"], email=analysis["email"])
        if order:
            return generate_llama_response(user_text, f"Order status: {order['fulfillment_status']}")

    elif intent == "delivery_policy":
        return "We deliver worldwide within 3–5 business days. Shipping is free on orders over $50."

    elif intent == "return_policy":
        return "Returns are accepted within 30 days. Items must be unused and in original packaging."

    return generate_generic_response(user_text)


if __name__ == '__main__':
    app.run(debug=True)
