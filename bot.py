"""
Sakhva Travel — WhatsApp бот
GREEN-API + Flask webhook

Функции:
1. Автоответ на входящие сообщения
2. Отправка подтверждения бронирования
3. Напоминание за день до тура
"""

import requests
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# ── CONFIG ──
INSTANCE = '7107579885'
TOKEN    = '813d22a2e8d94f9fb830ad1edbfd44d6537234adb0dc4f35a9'
BASE_URL = f'https://api.green-api.com/waInstance{INSTANCE}'
GUIDE_PHONE = '995511272623'  # номер Тимура для уведомлений

app = Flask(__name__)

# ── ОТПРАВКА СООБЩЕНИЯ ──
def send_message(phone: str, text: str):
    """phone = '79991234567' или '995511272623' (без +)"""
    chat_id = f'{phone}@c.us'
    r = requests.post(
        f'{BASE_URL}/sendMessage/{TOKEN}',
        json={'chatId': chat_id, 'message': text}
    )
    return r.json()

# ── АВТООТВЕТЫ ──
KEYWORDS = {
    ('цена', 'стоит', 'сколько', 'price', 'cost'): """💰 *Цены на туры 2026:*

• Казбеги за 1 день — от €45/чел
• Частный тур по Тбилиси — от €35/чел
• Кахетия / Сигнаги — от €50/чел
• Мцхета — от €35/чел

Цена включает: транспорт, гид, все входы.
Оплата в день тура — наличными или картой.

Хотите забронировать? Напишите удобную дату 📅""",

    ('казбег', 'kazbeg', 'гора', 'гдзе', 'гори'): """🏔 *Тур в Казбеги*

Выезд из Тбилиси в 08:00, возврат ~20:00.
Маршрут: Военно-Грузинская дорога → Степанцминда → Церковь Гергети (2170м)

От €45/чел | Макс. 6 человек
Бесплатный перенос при плохой погоде ☁️

Укажите дату и количество человек — подтвержу свободные места!""",

    ('свобод', 'есть места', 'доступен', 'available', 'free'): """📅 Напишите удобную дату и количество человек — проверю наличие мест и отвечу за 15 минут!

Работаю ежедневно 08:00–22:00 🕗""",

    ('привет', 'здравствуй', 'добрый', 'hello', 'hi', 'хай'): """👋 Привет! Я Тимур — частный русскоязычный гид по Грузии.

Туры 2026:
🏔 Казбеги за 1 день — €45+
🏛 Тбилиси скрытые места — €35+
🍷 Кахетия и вино — €50+
🕌 Мцхета — €35+

Что вас интересует?""",

    ('отмен', 'cancel', 'перенес', 'reschedule'): """✅ *Политика отмены:*

Бесплатная отмена за 24 часа — без вопросов и штрафов.

Для Казбеги: если плохая погода — Тимур сам предложит перенос бесплатно.
Количество переносов не ограничено.

Напишите вашу дату — оформим перенос! 📅""",
}

def get_auto_reply(text: str):
    text_lower = text.lower()
    for keywords, reply in KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return reply
    return None

# ── WEBHOOK — входящие сообщения ──
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({'ok': True})

    type_ = data.get('typeWebhook')

    # Входящее сообщение
    if type_ == 'incomingMessageReceived':
        msg = data.get('messageData', {})
        text = msg.get('textMessageData', {}).get('textMessage', '')
        sender = data.get('senderData', {}).get('sender', '')
        sender_name = data.get('senderData', {}).get('senderName', 'Гость')
        phone = sender.replace('@c.us', '')

        print(f'[{datetime.now().strftime("%H:%M")}] {sender_name} ({phone}): {text}')

        # Автоответ
        reply = get_auto_reply(text)
        if reply and phone != GUIDE_PHONE:
            send_message(phone, reply)

        # Уведомить Тимура о новом сообщении
        notify_guide(sender_name, phone, text)

    return jsonify({'ok': True})


def notify_guide(name: str, phone: str, text: str):
    """Пересылает новое сообщение Тимуру"""
    msg = f'📩 *Новое сообщение*\n👤 {name} (+{phone})\n💬 {text}'
    send_message(GUIDE_PHONE, msg)


# ── ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ ──
def send_booking_confirmation(phone: str, name: str, tour: str, date: str, people: int, price: float):
    msg = f"""✅ *Бронирование подтверждено!*

👤 {name}
🗺 Тур: {tour}
📅 Дата: {date}
👥 Человек: {people}
💰 Сумма: €{price}

📍 Встречаемся у вас в отеле / удобном месте.
Тимур свяжется с вами за день до тура.

Бесплатная отмена за 24 часа.
По вопросам: +995 511 272 623"""
    return send_message(phone, msg)


# ── НАПОМИНАНИЕ ЗА ДЕНЬ ──
def send_reminder(phone: str, name: str, tour: str, date: str, meetup: str):
    msg = f"""🔔 *Напоминание о туре завтра!*

Привет, {name}!

🗺 *{tour}*
📅 Дата: {date}
🕗 Встреча: {meetup}

Что взять:
• Удобная обувь
• Вода и перекус
• Паспорт (для Казбеги)
• Тёплая куртка (горы)

Увидимся завтра! 🇬🇪
Тимур: +995 511 272 623"""
    return send_message(phone, msg)


# ── ЗАПУСК ──
if __name__ == '__main__':
    print('Sakhva Travel WhatsApp Bot запущен...')
    print(f'Webhook: POST /webhook')
    app.run(host='0.0.0.0', port=5000, debug=True)
