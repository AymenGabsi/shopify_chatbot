# Shopify AI Chatbot - Flask App

from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOP = os.getenv("SHOPIFY_STORE_NAME")

app = Flask(__name__)
CORS(app)  # Enable CORS for external calls



@app.route('/')
def index():
    return "Shopify AI Chatbot Backend is running."


@app.route('/script.js')
def serve_script_tag():
    return """
(function() {
  if (window.__chatbot_injected) return;
  window.__chatbot_injected = true;

  const div = document.createElement("div");
  div.innerHTML = `<style>
    #chat-widget { position: fixed; bottom: 20px; right: 20px; width: 340px; height: 450px;
      background: white; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      font-family: 'Arial', sans-serif; z-index: 9999; display: flex; flex-direction: column; overflow: hidden; }
    #chat-header { background: #111; color: white; padding: 12px; font-size: 16px; text-align: center; }
    #chat-messages { flex: 1; padding: 10px; overflow-y: auto; font-size: 14px; }
    #chat-input-area { display: flex; border-top: 1px solid #eee; }
    #chat-input { flex: 1; border: none; padding: 10px; font-size: 14px; }
    #chat-send { background: #111; color: white; border: none; padding: 10px 15px; cursor: pointer; }
    .typing { font-style: italic; color: gray; }
    .product-card { border: 1px solid #eee; border-radius: 8px; padding: 10px; margin: 5px 0; background: #f9f9f9; }
    .product-card img { width: 100%; border-radius: 6px; }
  </style>
  <div id='chat-widget'>
    <div id='chat-header'>🛍️ Chat with us</div>
    <div id='chat-messages'></div>
    <div id='chat-input-area'>
      <input id='chat-input' placeholder='Ask me anything...' />
      <button id='chat-send'>Send</button>
    </div>
  </div>`;

  document.body.appendChild(div);

  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');
  const sendBtn = document.getElementById('chat-send');
  const BACKEND_URL = 'https://your-backend-url.onrender.com/api/chat';

  function addMessage(sender, text, isHTML = false) {
    const p = document.createElement('div');
    p.innerHTML = `<strong>${sender}:</strong> ` + (isHTML ? text : escapeHtml(text));
    messages.appendChild(p);
    messages.scrollTop = messages.scrollHeight;
  }

  function escapeHtml(str) {
    return str.replace(/[&<>"]'/g, m =>
      ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'}[m])
    );
  }

  function showTyping() {
    const typing = document.createElement('div');
    typing.id = 'typing';
    typing.className = 'typing';
    typing.textContent = 'Bot is typing...';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;
  }

  function hideTyping() {
    const typing = document.getElementById('typing');
    if (typing) typing.remove();
  }

  sendBtn.onclick = async () => {
    const msg = input.value.trim();
    if (!msg) return;
    addMessage('You', msg);
    input.value = '';
    showTyping();
    try {
      const res = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
      });
      const data = await res.json();
      hideTyping();
      addMessage('Bot', data.reply, true);
    } catch (err) {
      hideTyping();
      addMessage('Bot', 'Sorry, something went wrong.');
    }
  };
})();
    """, 200, {'Content-Type': 'application/javascript'}



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

Message: "{user_message}"
"""
    messages = [
        {"role": "system", "content": "You extract intent and relevant data from customer messages."},
        {"role": "user", "content": prompt}
    ]
    content = call_llama(messages)
    result = {"intent": "generic", "product_name": None, "order_id": None, "email": None}
    for line in content.splitlines():
        if line.startswith("intent:"): result["intent"] = line.split(":", 1)[1].strip()
        if line.startswith("product_name:"): result["product_name"] = line.split(":", 1)[1].strip()
        if line.startswith("order_id:"): result["order_id"] = line.split(":", 1)[1].strip()
        if line.startswith("email:"): result["email"] = line.split(":", 1)[1].strip()
    return result


def get_product_details(product_name):
    url = f"https://{SHOP}/admin/api/2024-04/products.json?title={product_name}"
    res = requests.get(url, headers={"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}, verify=False)
    data = res.json()
    return data['products'][0] if data['products'] else None


def extract_requested_info(product, info_type):
    variant = product['variants'][0]
    if info_type == "price":
        return f"The price is {variant['price']} {variant.get('currency', 'USD')}."
    elif info_type == "stock":
        return f"{variant['inventory_quantity']} units in stock."
    elif info_type == "color":
        return f"Available colors: {', '.join([v['option1'] for v in product['variants']])}."
    elif info_type == "size":
        return f"Sizes: {', '.join(set([v['option2'] for v in product['variants'] if v['option2']]))}."
    else:
        return "I couldn’t find that information."


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
        {"role": "system", "content": "You are a friendly AI assistant for a Shopify store."},
        {"role": "user", "content": f"Customer question: {user_message}\n\nData: {extracted_info}"}
    ]
    return call_llama(messages)


def generate_generic_response(user_message):
    return call_llama([
        {"role": "system", "content": "You are a helpful assistant for a fashion store."},
        {"role": "user", "content": user_message}
    ])


@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    analysis = classify_intent_and_entities(user_message)

    intent = analysis["intent"]

    if intent == "product_info" and analysis["product_name"]:
        product = get_product_details(analysis["product_name"])
        if product:
            info = extract_requested_info(product, analysis.get("info", "price"))
            reply = generate_llama_response(user_message, info)
            return jsonify({"reply": reply})

    elif intent == "order_status" and (analysis["order_id"] or analysis["email"]):
        order = get_order_info(order_id=analysis["order_id"], email=analysis["email"])
        if order:
            info = f"Your order '{order['name']}' is currently '{order['fulfillment_status'] or 'unfulfilled'}'."
            reply = generate_llama_response(user_message, info)
            return jsonify({"reply": reply})

    elif intent == "delivery_policy":
        return jsonify({"reply": "We deliver worldwide within 3–5 business days. Shipping is free on orders over $50."})

    elif intent == "return_policy":
        return jsonify({"reply": "Returns are accepted within 30 days of purchase. Products must be unused and in original packaging."})

    else:
        reply = generate_generic_response(user_message)
        return jsonify({"reply": reply})


if __name__ == '__main__':
    app.run(debug=True)
