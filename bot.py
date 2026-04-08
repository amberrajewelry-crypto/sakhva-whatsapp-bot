"""
Sakhva Travel — WhatsApp бот (polling mode) v5
GREEN-API getNotification + диалоговые состояния
"""
import requests
import time
import threading
import datetime
import re
from flask import Flask, jsonify

INSTANCE    = '7107579885'
TOKEN       = '813d22a2e8d94f9fb830ad1edbfd44d6537234adb0dc4f35a9'
BASE_URL    = f'https://api.green-api.com/waInstance{INSTANCE}'
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

# ──────────────────────────────────────────────
# Тексты туров
# ──────────────────────────────────────────────

MSG_GREETING = """👋 Привет! Я Тимур — частный гид по Грузии 🇬🇪

Мои туры 2026:
1️⃣ Казбеги за 1 день — от €45
2️⃣ Скрытые места Тбилиси — от €35
3️⃣ Старый Тбилиси — от €25
4️⃣ Кахетия / Сигнаги — от €45
5️⃣ Мцхета — от €14
6️⃣ Ночной Тбилиси — от €25
7️⃣ Советский Тбилиси — от €30
8️⃣ Фототур по Тбилиси
9️⃣ Ужин с видом на Тбилиси

Напишите номер тура или название — расскажу подробнее! 😊"""

MSG_TOURS_LIST = """🇬🇪 *Туры по Грузии 2026:*

1️⃣ Казбеги за 1 день — от €45/чел
2️⃣ Скрытые места Тбилиси — от €35/чел
3️⃣ Старый Тбилиси — от €25/чел
4️⃣ Кахетия / Сигнаги — от €45/чел
5️⃣ Мцхета — от €14/чел
6️⃣ Ночной Тбилиси — от €25/чел
7️⃣ Советский Тбилиси — от €30/чел
8️⃣ Фототур по Тбилиси
9️⃣ Ужин с видом на Тбилиси

Напишите номер или название тура 👆"""

TOURS = {
    'казбег': {
        'name': 'Казбеги за 1 день',
        'msg': """🏔 *Казбеги за 1 день*

Маршрут: ВГД → Степанцминда → церковь Гергети (2170м)
Выезд 08:00 из центра Тбилиси, возврат ~22:00

💰 От €45/чел · до 6 человек
☁️ Бесплатный перенос при плохой погоде
📍 Включено: трансфер, гид весь день, входные билеты

Укажите дату и количество человек — забронирую! 📅"""
    },
    'скрыт': {
        'name': 'Скрытые места Тбилиси',
        'msg': """🏛 *Скрытые места Тбилиси*

Нетуристический Тбилиси: дворы-колодцы, старые бани, рынок Дезертиров, виды с крыш.
Длительность: ~4 часа пешком

💰 От €35/чел · до 6 человек
🚶 Пешеходный тур по центру города

Укажите дату и количество человек 📅"""
    },
    'старый тбилис': {
        'name': 'Старый Тбилиси',
        'msg': """🕌 *Экскурсия по Старому Тбилиси*

Нарикала, серные бани, Метехи, Авлабари, мечеть и синагога рядом.
Длительность: ~3 часа

💰 От €25/чел · до 6 человек

Укажите дату и количество человек 📅"""
    },
    'кахет': {
        'name': 'Кахетия / Сигнаги',
        'msg': """🍷 *Кахетия и Сигнаги*

Город любви Сигнаги, монастырь Бодбе, дегустация вина.
Выезд 09:00 из Тбилиси, возврат ~20:00

💰 От €45/чел · до 6 человек
🍾 Включено: дегустация вина

Укажите дату и количество человек 📅"""
    },
    'сигнаг': {
        'name': 'Кахетия / Сигнаги',
        'msg': """🍷 *Кахетия и Сигнаги*

Город любви Сигнаги, монастырь Бодбе, дегустация вина.
Выезд 09:00 из Тбилиси, возврат ~20:00

💰 От €45/чел · до 6 человек
🍾 Включено: дегустация вина

Укажите дату и количество человек 📅"""
    },
    'мцхет': {
        'name': 'Мцхета',
        'msg': """🕌 *Мцхета — древняя столица Грузии*

Собор Светицховели, монастырь Джвари над слиянием рек.
Длительность: ~3 часа, 20 км от Тбилиси

💰 От €14/чел · до 6 человек

Укажите дату и количество человек 📅"""
    },
    'ночной': {
        'name': 'Ночной Тбилиси',
        'msg': """🌙 *Ночной Тбилиси*

Канатная дорога, крепость Нарикала, набережная Куры, лучшие крыши.
Старт в 19:00, длительность ~3 часа

💰 От €25/чел · до 6 человек

Укажите дату и количество человек 📅"""
    },
    'советск': {
        'name': 'Советский Тбилиси',
        'msg': """🏗 *Советский Тбилиси*

Сталинский ампир, конструктивизм, легенды и быт советской Грузии.
Уникальный взгляд на историю города.

💰 От €30/чел · до 6 человек

Укажите дату и количество человек 📅"""
    },
    'фото': {
        'name': 'Фототур по Тбилиси',
        'msg': """📸 *Фототур по Тбилиси*

Лучшие локации для съёмки: крыши, дворы, рассвет над городом, Нарикала.
Ранний выезд для золотого света.

Укажите дату и количество человек 📅"""
    },
    'ужин': {
        'name': 'Ужин с видом на Тбилиси',
        'msg': """🍽 *Ужин с видом на Тбилиси*

Ресторан с панорамным видом, грузинская кухня, вино.
Я рекомендую лучшие места без туристической наценки.

Укажите дату и количество человек 📅"""
    },
    'digital': {
        'name': 'Digital Nomad Tour',
        'msg': """💻 *Digital Nomad Tour*

Лучшие коворкинги, кафе с Wi-Fi, районы для жизни, SIM-карты и банки.
Практический тур для переехавших и удалёнщиков.

💰 Уточните при записи

Укажите дату 📅"""
    },
    'эмигрант': {
        'name': 'Тур для эмигрантов',
        'msg': """🏠 *Тур для эмигрантов*

Банки, SIM-карты, районы для жизни, нетуристические кафе.
4 часа практического Тбилиси для переехавших.

💰 Уточните при записи

Укажите дату 📅"""
    },
    'slow': {
        'name': 'Slow Travel Тбилиси',
        'msg': """🌿 *Slow Travel Тбилиси*

Неспешный тур без толпы: рынки, дворики, разговоры с местными, кофе в старых кафе.

💰 Уточните при записи

Укажите дату 📅"""
    },
}

MSG_PRICE = """💰 *Цены на туры 2026:*

🏔 Казбеги — от €45/чел
🏛 Скрытые места Тбилиси — от €35/чел
🕌 Старый Тбилиси — от €25/чел
🍷 Кахетия / Сигнаги — от €45/чел
🕌 Мцхета — от €14/чел
🌙 Ночной Тбилиси — от €25/чел
🏗 Советский Тбилиси — от €30/чел

Оплата в день тура — наличными или картой. Предоплаты нет.
Напишите какой тур интересует 📅"""

MSG_CANCEL = """✅ *Политика отмены:*

Бесплатная отмена за 24 часа — без штрафов.
Казбеги: бесплатный перенос при плохой погоде ☁️
Переносов неограниченно. Предоплаты нет.

Напишите дату — оформим! 📅"""

MSG_DATE = """📅 Напишите удобную дату и количество человек — проверю наличие мест и отвечу за 15 минут!

Работаю ежедневно 08:00–22:00 🕗"""

MSG_THANKS = """Пожалуйста! 😊 Буду рад встретить вас в Грузии 🇬🇪

По любым вопросам — пишите!"""

MSG_BOOKING_CONFIRM = """✅ Отлично, записываю вас!

Тимур свяжется за день до тура для подтверждения места встречи.
Оплата в день тура — наличными или картой.
Бесплатная отмена за 24 часа.

До встречи в Грузии! 🇬🇪"""

# ──────────────────────────────────────────────
# Состояния диалога: phone → {'state', 'tour'}
# ──────────────────────────────────────────────
user_states = {}

DATE_PATTERNS = [
    r'\b\d{1,2}[./]\d{1,2}',           # 15.04 / 15/04
    r'\b\d{1,2}\s+(янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)',
    r'завтра|послезавтра|на этой неделе|на следующей',
    r'\b(январ|феврал|март|апрел|май|июн|июл|август|сентябр|октябр|ноябр|декабр)',
    r'\b\d{4}\b',                        # год типа 2026
]

def has_date(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in DATE_PATTERNS)

def has_people(text: str) -> bool:
    t = text.lower()
    return bool(re.search(r'\b\d+\s*(чел|человек|люд|person|people)\b', t)) or \
           bool(re.search(r'\b[12345678]\b', t))

def get_tour_by_keyword(text: str):
    t = text.lower()
    for kw, tour in TOURS.items():
        if kw in t:
            return tour
    return None

def process_message(phone: str, text: str, name: str):
    """Возвращает (auto_reply или None, forward_to_guide bool)"""
    t = text.lower()
    state = user_states.get(phone, {})

    # ── Состояние: ждём дату после выбора тура ──
    if state.get('state') == 'waiting_date':
        if has_date(text) or has_people(text):
            tour_name = state.get('tour', 'тур')
            user_states.pop(phone, None)
            return MSG_BOOKING_CONFIRM, True

    # ── Приветствие ──
    if any(kw in t for kw in ['привет','здравствуй','добрый','hello','hi','салам','хай','good morning','good day']):
        return MSG_GREETING, True

    # ── Конкретный тур ──
    tour = get_tour_by_keyword(text)
    if tour:
        user_states[phone] = {'state': 'waiting_date', 'tour': tour['name']}
        return tour['msg'], True

    # ── Номер тура из списка (1-9) ──
    tour_by_num = {
        '1': TOURS['казбег'],
        '2': TOURS['скрыт'],
        '3': TOURS['старый тбилис'],
        '4': TOURS['кахет'],
        '5': TOURS['мцхет'],
        '6': TOURS['ночной'],
        '7': TOURS['советск'],
        '8': TOURS['фото'],
        '9': TOURS['ужин'],
    }
    stripped = text.strip()
    if stripped in tour_by_num:
        tour = tour_by_num[stripped]
        user_states[phone] = {'state': 'waiting_date', 'tour': tour['name']}
        return tour['msg'], True

    # ── Цена ──
    if any(kw in t for kw in ['цена','стоит','сколько','price','cost','€','eur','почём']):
        return MSG_PRICE, True

    # ── Дата/наличие мест ──
    if any(kw in t for kw in ['свобод','есть места','available','когда','дата','число']):
        return MSG_DATE, True

    # ── Отмена ──
    if any(kw in t for kw in ['отмен','cancel','перенес','reschedule','отказ']):
        return MSG_CANCEL, True

    # ── Спасибо ──
    if any(kw in t for kw in ['спасибо','thanks','thank','благодар']):
        return MSG_THANKS, True

    # ── Туры / общий запрос ──
    if any(kw in t for kw in ['тур','tour','грузи','georgia','tbilisi','тбилис','экскурс','маршрут']):
        return MSG_TOURS_LIST, True

    return None, True  # нет автоответа, но пересылаем Тимуру

# ──────────────────────────────────────────────
# Статистика
# ──────────────────────────────────────────────
processed_ids = set()
stats = {'received': 0, 'replied': 0, 'forwarded': 0, 'started_at': None}

# ──────────────────────────────────────────────
# Polling
# ──────────────────────────────────────────────
def poll_messages():
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
                # поддержка обычного и расширенного текста
                text = (msg_data.get('textMessageData', {}).get('textMessage', '') or
                        msg_data.get('extendedTextMessageData', {}).get('text', ''))
                sender = body.get('senderData', {}).get('sender', '')
                name   = body.get('senderData', {}).get('senderName', 'Гость')
                phone  = sender.replace('@c.us', '')

                if receipt_id not in processed_ids and text and phone != GUIDE_PHONE:
                    processed_ids.add(receipt_id)
                    stats['received'] += 1
                    print(f'[{name}] {text}')

                    reply, do_forward = process_message(phone, text, name)

                    if reply:
                        time.sleep(1.5)
                        send_message(phone, reply)
                        stats['replied'] += 1
                        print(f'→ Автоответ отправлен')

                    if do_forward:
                        send_message(GUIDE_PHONE, f'📩 *{name}* (+{phone}):\n{text}')
                        stats['forwarded'] += 1

            if receipt_id:
                requests.delete(f'{BASE_URL}/deleteNotification/{TOKEN}/{receipt_id}', timeout=5)

        except Exception as e:
            print(f'Poll error: {e}')
            time.sleep(3)


# ──────────────────────────────────────────────
# API для Тимура: ручная отправка напоминаний
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
        'version': 'v5-dialog',
        'polling': stats['started_at'] is not None,
        'started_at': stats['started_at'],
        'received': stats['received'],
        'replied': stats['replied'],
        'forwarded': stats['forwarded'],
        'active_dialogs': len(user_states),
    })

@app.route('/')
def index():
    return jsonify({'status': 'Sakhva Travel WhatsApp Bot v5'})


# Старт polling при импорте (gunicorn-совместимо)
_t = threading.Thread(target=poll_messages, daemon=True)
_t.start()
print('Polling started!')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
