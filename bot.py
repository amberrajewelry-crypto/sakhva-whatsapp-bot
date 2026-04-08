"""
Sakhva Travel — WhatsApp бот v6
AI-ядро: GPT-4o-mini отвечает на любые вопросы
GREEN-API polling (бесплатный тариф)
"""
import os
import requests
import time
import threading
import datetime
from flask import Flask, jsonify
from openai import OpenAI

INSTANCE    = '7107579885'
TOKEN       = '813d22a2e8d94f9fb830ad1edbfd44d6537234adb0dc4f35a9'
BASE_URL    = f'https://api.green-api.com/waInstance{INSTANCE}'
GUIDE_PHONE = '995511272623'

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__)

# ──────────────────────────────────────────────
# Системный промпт — вся база знаний о турах
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """Ты — Тимур, частный русскоязычный гид по Грузии из Тбилиси.
Ты отвечаешь клиентам в WhatsApp. Отвечай дружелюбно, кратко (не более 5-6 предложений), используй эмодзи.
Никогда не говори что ты ИИ или бот. Ты Тимур.

ТВОИ ТУРЫ 2026:
1. Казбеги за 1 день — от €45/чел (₾128)
   • Выезд 08:00 из Тбилиси, возврат ~22:00
   • Маршрут: Военно-Грузинская дорога → Степанцминда → церковь Гергети (2170м)
   • Включено: трансфер, гид, входные билеты
   • Бесплатный перенос при плохой погоде

2. Скрытые места Тбилиси — от €35/чел (₾100)
   • ~4 часа пешком. Дворы-колодцы, старые бани, рынок Дезертиров, виды с крыш

3. Старый Тбилиси — от €25/чел (₾71)
   • ~3 часа. Нарикала, серные бани, Метехи, Авлабари, мечеть и синагога рядом

4. Кахетия / Сигнаги — от €45/чел (₾128)
   • Выезд 09:00, возврат ~20:00. Город любви Сигнаги, монастырь Бодбе, дегустация вина

5. Мцхета — от €14/чел (₾40)
   • ~3 часа, 20 км от Тбилиси. Собор Светицховели, монастырь Джвари

6. Ночной Тбилиси — от €25/чел (₾71)
   • Старт 19:00, ~3 часа. Канатная дорога, Нарикала, набережная Куры

7. Советский Тбилиси — от €30/чел (₾86)
   • Сталинский ампир, конструктивизм, советская история Грузии

8. Фототур по Тбилиси — цена по запросу
   • Лучшие локации для съёмки, ранний выезд для золотого света

9. Ужин с видом на Тбилиси — цена по запросу
   • Лучшие рестораны с панорамным видом, грузинская кухня, вино

10. Digital Nomad Tour — цена по запросу
    • Коворкинги, кафе с Wi-Fi, SIM-карты, банки, районы для жизни

11. Тур для эмигрантов — цена по запросу
    • Практический тур для переехавших: банки, карты, районы, нетуристические кафе

12. Slow Travel Тбилиси — цена по запросу
    • Неспешный тур: рынки, дворики, разговоры с местными

ВАЖНАЯ ИНФОРМАЦИЯ:
• Группы до 6 человек (приватный тур)
• Оплата в день тура — наличными (GEL, USD, EUR) или картой
• Предоплата НЕ нужна
• Бесплатная отмена за 24 часа — без штрафов
• Бесплатный перенос при плохой погоде (Казбеги)
• Работаю ежедневно 08:00–22:00
• Отвечаю за 15 минут

БРОНИРОВАНИЕ:
Когда клиент называет тур и дату — скажи: "Отлично! Записываю вас. Тимур свяжется за день до тура для подтверждения деталей. Оплата в день тура. До встречи в Грузии! 🇬🇪"

ЯЗЫК:
Отвечай на том языке, на котором пишет клиент (русский, английский, грузинский).
Если вопрос не про туры — вежливо переведи разговор к теме туров.
"""

# ──────────────────────────────────────────────
# История диалогов: phone → [messages]
# ──────────────────────────────────────────────
conversations = {}  # phone -> list of {role, content}
MAX_HISTORY = 10    # последних сообщений

def get_ai_reply(phone: str, user_text: str) -> str:
    if phone not in conversations:
        conversations[phone] = []

    history = conversations[phone]
    history.append({'role': 'user', 'content': user_text})

    # Обрезаем историю до MAX_HISTORY
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
        conversations[phone] = history

    if not ai:
        return 'Привет! Я Тимур — гид по Грузии 🇬🇪 Напишите что интересует!'
    try:
        resp = ai.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'system', 'content': SYSTEM_PROMPT}] + history,
            max_tokens=400,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content.strip()
        history.append({'role': 'assistant', 'content': reply})
        return reply
    except Exception as e:
        print(f'AI error: {e}')
        return ('Привет! Я Тимур — гид по Грузии 🇬🇪 Пишу вам чуть позже, сейчас на туре. '
                'Или звоните: +995 511 272 623')

# ──────────────────────────────────────────────
# GREEN-API
# ──────────────────────────────────────────────
def send_message(phone: str, text: str):
    try:
        r = requests.post(
            f'{BASE_URL}/sendMessage/{TOKEN}',
            json={'chatId': f'{phone}@c.us', 'message': text},
            timeout=10
        )
        return r.json()
    except Exception as e:
        print(f'Send error: {e}')

processed_ids = set()
stats = {'received': 0, 'replied': 0, 'forwarded': 0, 'started_at': None}

def poll_messages():
    stats['started_at'] = datetime.datetime.utcnow().isoformat()
    print('Polling started (v6-AI)...')
    while True:
        try:
            r = requests.get(f'{BASE_URL}/receiveNotification/{TOKEN}', timeout=25)
            data = r.json()
            if not data:
                time.sleep(1)
                continue

            receipt_id = data.get('receiptId')
            body = data.get('body', {})
            type_ = body.get('typeWebhook', '')

            if type_ == 'incomingMessageReceived':
                msg_data = body.get('messageData', {})
                text = (msg_data.get('textMessageData', {}).get('textMessage', '') or
                        msg_data.get('extendedTextMessageData', {}).get('text', ''))
                sender = body.get('senderData', {}).get('sender', '')
                name   = body.get('senderData', {}).get('senderName', 'Гость')
                phone  = sender.replace('@c.us', '')

                if receipt_id not in processed_ids and text and phone != GUIDE_PHONE:
                    processed_ids.add(receipt_id)
                    stats['received'] += 1
                    print(f'[{name}] {text}')

                    # AI-ответ
                    reply = get_ai_reply(phone, text)
                    time.sleep(1.5)
                    send_message(phone, reply)
                    stats['replied'] += 1
                    print(f'→ AI ответил: {reply[:60]}...')

                    # Уведомить Тимура
                    send_message(GUIDE_PHONE, f'📩 *{name}* (+{phone}):\n{text}')
                    stats['forwarded'] += 1

            if receipt_id:
                requests.delete(f'{BASE_URL}/deleteNotification/{TOKEN}/{receipt_id}', timeout=5)

        except Exception as e:
            print(f'Poll error: {e}')
            time.sleep(3)


# ──────────────────────────────────────────────
# Ручные функции для Тимура
# ──────────────────────────────────────────────
def send_booking_confirmation(phone, name, tour, date, people, price):
    msg = f"""✅ *Бронирование подтверждено!*

👤 {name}
🗺 {tour}
📅 {date}
👥 {people} чел.
💰 €{price}

Тимур свяжется за день до тура.
Бесплатная отмена за 24 часа."""
    return send_message(phone, msg)

def send_reminder(phone, name, tour, date, meetup):
    msg = f"""🔔 *Напоминание — тур завтра!*

{name}, ждём вас!
🗺 {tour}
📅 {date} · {meetup}

Возьмите: удобную обувь, воду, паспорт (Казбеги), куртку.
Тимур: +995 511 272 623 🇬🇪"""
    return send_message(phone, msg)


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': 'v6-AI',
        'polling': stats['started_at'] is not None,
        'started_at': stats['started_at'],
        'received': stats['received'],
        'replied': stats['replied'],
        'forwarded': stats['forwarded'],
        'active_dialogs': len(conversations),
    })

@app.route('/')
def index():
    return jsonify({'status': 'Sakhva Travel WhatsApp Bot v6-AI'})


# Старт polling при импорте (gunicorn-совместимо)
_t = threading.Thread(target=poll_messages, daemon=True)
_t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
