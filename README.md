# 🤖 Botify – AI-Powered WhatsApp Chatbot for Shopify

Botify is a full-stack AI chatbot built with Python, Flask, and PostgreSQL. It connects to a Shopify store and intelligently responds to WhatsApp messages from users using LLaMA 3 via Groq API. The bot handles product inquiries, order statuses, delivery/return policies, and more — with memory and context awareness.

---

## 🚀 Features

- 🔗 **Shopify Integration**: fetch product, stock, and order info via Admin API
- 💬 **WhatsApp Messaging**: connect with Meta's Cloud API
- 🧠 **AI Responses via Groq (LLaMA 3)**: answer questions naturally and contextually
- 🧾 **Contextual Memory**: stores conversation history in PostgreSQL
- 🔐 **Secure Webhook Handling**: validates Meta requests
- 🌐 **Deployable on Render**: full Render-compatible stack

---

## 📦 Tech Stack

| Layer         | Tool                     |
|---------------|--------------------------|
| Backend       | Flask (Python)           |
| AI Model      | LLaMA 3 via Groq API     |
| Messaging     | WhatsApp Cloud API (Meta)|
| Database      | PostgreSQL (Render)      |
| ORM           | SQLAlchemy               |
| Hosting       | Render.com               |

---

## 📁 Project Structure

```
.
├── botify.py             # Main Flask app
├── models.py             # SQLAlchemy DB model (Message)
├── .env                  # Environment variables (not committed)
├── requirements.txt      # Dependencies
├── README.md             # You are here
```

---

## ⚙️ Environment Setup

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
GROQ_API_KEY=your_groq_api_key
SHOPIFY_ACCESS_TOKEN=your_shopify_token
META_TOKEN=your_meta_whatsapp_token
PHONE_NUMBER_ID=your_whatsapp_number_id
VERIFY_TOKEN=your_webhook_verify_token
```

---

## 🛠️ Installation

1. Clone the repo:

```bash
git clone https://github.com/yourusername/botify.git
cd botify
```

2. Create virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Run locally for testing:

```bash
python botify.py
```

4. Optional: Test DB connection

```bash
curl http://localhost:5000/health
```

---

## 🧠 LLaMA Prompt Behavior

The assistant is grounded with a strict prompt:

> "Only respond using the information provided. Do NOT guess or refer users elsewhere."

Contextual history is pulled from PostgreSQL and passed along with each message.

---

## 🧪 Testing on WhatsApp

1. Register your app on [Meta Developer Portal](https://developers.facebook.com/)
2. Add a webhook URL pointing to `https://your-app.onrender.com/webhook`
3. Set `VERIFY_TOKEN` to match what’s in your `.env`
4. Register your WhatsApp test number
5. Start chatting!

---

## ☁️ Deploy on Render

1. Create a **Web Service** on [Render.com](https://render.com)
2. Point it to this repo
3. Add all `.env` variables in Render dashboard
4. (Optional) Create a PostgreSQL database via Render and update `DATABASE_URL`

---

## 📬 Webhook Endpoints

| Method | Endpoint        | Description                      |
|--------|------------------|----------------------------------|
| GET    | `/webhook`       | Meta verification handshake      |
| POST   | `/webhook`       | Receives WhatsApp messages       |
| GET    | `/health`        | Tests DB connection              |

---

## 📓 Sample Message Flow

1. User: “Do you have the Urban Denim Jacket?”
2. Bot: fetches product info from Shopify + previous context
3. Bot: “Yes, it’s available in Blue, Black, and Grey, sizes M to XL.”

---

## 📃 License

This project is open-source under the [MIT License](LICENSE).

---

## ✨ Credits

Built with ❤️ by Aymen Gabsi  
Integrated using: [Groq](https://groq.com), [Shopify Admin API](https://shopify.dev/docs/api), and [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp)
