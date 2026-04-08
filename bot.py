"""
Sakhva Travel — WhatsApp бот (polling mode)
GREEN-API getNotification — работает на бесплатном тарифе
"""
import requests
import time
import threading
from flask import Flask, request, jsonify

INSTANCE = '7107579885'
TOKEN    = '813d22a2e8d94f9fb830ad1edbfd44d6537234adb0dc4f35a9'
BASE_URL = f'https://api.green-api.com/waInstance{INSTANCE}'
GUIDE_PHONE = '995511272623'

app = Flask(__name__)

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

KEYWORDS = {
    ('цена','стоит','сколько','price','cost','€','eur'): """💰 *Цены на туры 2026:*

• Казбеги за 1 день — от €45/чел
• Тбилиси скрытые места — от €35/чел
• Кахетия / Сигнаги — от €50/чел
• Мцхета — от €35/чел

Оплата в день тура — наличными или картой.
Напишите дату и количество человек 📅""",

    ('казбег','kazbeg'): """🏔 *Тур в Казбеги*

Выезд из Тбилиси 08:00, возврат ~20:00
Маршрут: ВГД → Степанцминда → Гергети (2170м)

От €45/чел · до 6 человек
Бесплатный перенос при плохой погоде ☁️

Укажите дату и кол-во человек!""",

    ('привет','здравствуй','добрый','hello','hi','салам','хай','good'): """👋 Привет! Я Тимур — частный гид по Грузии 🇬🇪

Туры 2026:
🏔 Казбеги — €45+
🏛 Тбилиси — €35+
🍷 Кахетия — €50+
🕌 Мцхета — €35+

Что вас интересует?""",

    ('отмен','cancel','перенес','reschedule'): """✅ *Политика отмены:*

Бесплатная отмена за 24 часа — без штрафов.
Казбеги: бесплатный перенос при плохой погоде.
Переносов неограниченно. Предоплаты нет.

Напишите дату — оформим! 📅""",

    ('свобод','есть места','available','когда','дата'): """📅 Напишите удобную дату и количество человек — проверю наличие мест и отвечу за 15 минут!

Работаю ежедневно 08:00–22:00 🕗""",

    ('спасибо','thanks','thank'): """Пожалуйста! 😊 Буду рад встретить вас в Грузии 🇬🇪

По любым вопросам — пишите!""",
}

processed_ids = set()
stats = {'received': 0, 'replied': 0, 'forwarded': 0, 'started_at': None}

def get_auto_reply(text: str):
    t = text.lower()
    for kws, reply in KEYWORDS.items():
        if any(kw in t for kw in kws):
            return reply
    return None

def poll_messages():
    import datetime
    stats['started_at'] = datetime.datetime.utcnow().isoformat()
    print('Polling started...')
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
                text = msg_data.get('textMessageData', {}).get('textMessage', '')
                sender = body.get('senderData', {}).get('sender', '')
                name = body.get('senderData', {}).get('senderName', 'Гость')
                phone = sender.replace('@c.us', '')

                if receipt_id not in processed_ids and text and phone != GUIDE_PHONE:
                    processed_ids.add(receipt_id)
                    stats['received'] += 1
                    print(f'[{name}] {text}')

                    reply = get_auto_reply(text)
                    if reply:
                        time.sleep(1.5)
                        send_message(phone, reply)
                        stats['replied'] += 1
                        print(f'→ Отправлен автоответ')

                    # Уведомить Тимура
                    send_message(GUIDE_PHONE, f'📩 *{name}* (+{phone}):\n{text}')
                    stats['forwarded'] += 1

            # Удаляем уведомление из очереди
            if receipt_id:
                requests.delete(f'{BASE_URL}/deleteNotification/{TOKEN}/{receipt_id}', timeout=5)

        except Exception as e:
            print(f'Poll error: {e}')
            time.sleep(3)


# Подтверждение бронирования
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

# Напоминание
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
        'bot': 'running',
        'polling': stats['started_at'] is not None,
        'started_at': stats['started_at'],
        'received': stats['received'],
        'replied': stats['replied'],
        'forwarded': stats['forwarded'],
        'version': 'v4-polling'
    })

@app.route('/')
def index():
    return jsonify({'status': 'Sakhva Travel WhatsApp Bot'})


# Запускаем polling при импорте модуля (работает и с gunicorn, и напрямую)
_t = threading.Thread(target=poll_messages, daemon=True)
_t.start()
print('Polling started!')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
