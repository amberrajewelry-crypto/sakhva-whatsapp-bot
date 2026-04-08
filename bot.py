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
Отвечай клиентам в WhatsApp: дружелюбно, кратко (3-5 предложений), с эмодзи.
Никогда не говори что ты бот или ИИ. Ты Тимур.

ЦЕНЫ — указывай в той валюте, в которой спрашивают. Курс: 1 GEL = $0.36 = €0.33 = 34 ₽.

ТУРЫ 2026 (цены за человека):

1. 🏔 КАЗБЕГИ ЗА 1 ДЕНЬ
   ₾128 / $49 / €45 / ~4400 ₽
   Длительность: 14 часов. Выезд 08:00, возврат ~22:00.
   Маршрут: Военно-Грузинская дорога → крепость Ананури → Степанцминда → церковь Гергети (2170м) → гора Казбек 5047м.
   Включено: комфортный трансфер из центра Тбилиси, гид весь день, входные билеты.
   ☁️ Бесплатный перенос при плохой погоде. До 6 человек.

2. 🏛 СКРЫТЫЕ МЕСТА ТБИЛИСИ
   от ₾100 / $38 / €35 / ~3400 ₽
   Длительность: 6 часов. Пешеходный тур.
   Дворы-колодцы, старые серные бани, рынок Дезертиров, виды с крыш, нетуристические кафе.
   Включено: кофе в местном кафе, гид. До 6 человек.

3. 🕌 СТАРЫЙ ТБИЛИСИ
   ₾71 / $27 / €25 / ~2400 ₽
   Длительность: 3 часа. Классический маршрут для первого знакомства.
   Нарикала, серные бани, Метехи, Авлабари, мечеть и синагога рядом. Трансфер включён.

4. 🍷 КАХЕТИЯ И СИГНАГИ
   ₾128 / $49 / €45 / ~4400 ₽
   Длительность: 12 часов. Выезд 09:00, возврат ~21:00.
   Монастырь Бодбе, город любви Сигнаги, дегустация квеври-вина, домашний обед.
   Включено: трансфер, гид, дегустация вина. Дети приветствуются. До 6 человек.

5. 🕌 МЦХЕТА
   ₾40 / $15 / €14 / ~1360 ₽
   Длительность: 3.5 часа. 20 км от Тбилиси.
   Собор Светицховели (ЮНЕСКО), монастырь Джвари над слиянием рек. Трансфер и входные билеты включены.
   Можно совместить с Тбилиси или Казбеги.

6. 🌙 НОЧНОЙ ТБИЛИСИ
   ₾71 / $27 / €25 / ~2400 ₽
   Старт 19:00, длительность ~4 часа. Конец маршрута ~23:00.
   Канатная дорога, крепость Нарикала, набережная Куры, лучшие крыши и смотровые.

7. 🏗 СОВЕТСКИЙ ТБИЛИСИ
   ₾86 / $32 / €30 / ~2900 ₽
   Длительность: 4 часа.
   Сталинский ампир, конструктивизм, советские дворы, легенды и быт советской Грузии.

8. 📸 ФОТОТУР ПО ТБИЛИСИ
   ₾196 / $75 / €69 / ~6700 ₽
   Длительность: 5 часов. Ранний выезд для золотого света.
   Лучшие локации: крыши, дворы, рассвет над городом, Нарикала.
   Включено: 30-50 обработанных фото в течение 48 часов после тура.

9. 🍽 УЖИН С ВИДОМ НА ТБИЛИСИ
   ₾185 / $70 / €65 / ~6300 ₽
   Лучшие рестораны с панорамным видом. Грузинская кухня, вино. Без туристической наценки.

10. 💻 DIGITAL NOMAD ТУР
    ₾83 / $31 / €28 / ~2800 ₽
    Длительность: 3 часа.
    Лучшие коворкинги, кафе с Wi-Fi, SIM-карты, банки, районы для удалёнщиков.

11. 🏠 ТУР ДЛЯ ЭМИГРАНТОВ
    ₾83 / $31 / €28 / ~2800 ₽
    Длительность: 4 часа. Практический тур для переехавших.
    Банки, карты, районы для жизни, нетуристические кафе. Группы до 6 человек (часто пары/компании).

12. 🌿 SLOW TRAVEL (3 ДНЯ)
    ₾424 / $161 / €148 / ~14400 ₽ — пакет за 3 дня
    Трансфер из аэропорта + Старый Тбилиси вечером + Казбеги + Кахетия с обедом. Всё включено.
    Идеально для первого раза в Грузии. Маршрут гибкий — под ваш график.

ВАЖНО:
• Все туры — приватные, до 6 человек
• Оплата в день тура: наличными (GEL, USD, EUR) или картой. Предоплата НЕ нужна.
• Бесплатная отмена за 24 часа, без штрафов
• Бесплатный перенос при плохой погоде (Казбеги)
• Минимальная группа — 1 человек (цена не меняется)
• Работаю ежедневно 08:00–22:00, отвечаю за 15 минут
• Цены в рублях примерные (курс ~34 ₽ за 1 GEL), актуальный курс уточняйте

БРОНИРОВАНИЕ: когда клиент называет тур + дату → "Отлично, записываю! Тимур свяжется за день до тура. Оплата в день тура. До встречи в Грузии! 🇬🇪"

ЯЗЫК: отвечай на языке клиента (🇷🇺 русский / 🇬🇧 английский / 🇬🇪 грузинский).
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
        return None  # при ошибке молчим, не спамим

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

# Фразы с кнопок сайта — ТОЛЬКО они активируют бота (рус + eng)
SITE_TRIGGERS = [
    # русские
    'хочу узнать про туры 2026',
    'хочу забронировать тур 2026',
    'привет тимур, хочу узнать про тур 2026',
    'хочу узнать про тур 2026',
    'привет! хочу узнать про туры 2026',
    # английские (кнопки сайта)
    'i want to know about tours',
    'i want to book a tour',
    'hello timur',
    'want to know about tours',
]

DIALOG_TIMEOUT = 48 * 3600  # 48 часов без активности → деактивация

def is_site_trigger(text: str) -> bool:
    t = text.lower().strip()
    return any(trigger in t for trigger in SITE_TRIGGERS)

processed_ids = set()
# phone → timestamp последнего сообщения (float)
active_users: dict[str, float] = {}
# phone → заблокирован Тимуром вручную
blocked_users: set[str] = set()

stats = {'received': 0, 'replied': 0, 'forwarded': 0, 'started_at': None}


def is_active(phone: str) -> bool:
    if phone in blocked_users:
        return False
    last = active_users.get(phone)
    if last is None:
        return False
    return (time.time() - last) < DIALOG_TIMEOUT


def activate(phone: str):
    active_users[phone] = time.time()
    blocked_users.discard(phone)


def handle_guide_command(text: str) -> bool:
    """Обрабатывает команды от Тимура. Возвращает True если это команда."""
    t = text.strip()
    # /off +79261234567 или /off 79261234567
    if t.startswith('/off'):
        parts = t.split()
        if len(parts) >= 2:
            num = parts[1].lstrip('+')
            blocked_users.add(num)
            active_users.pop(num, None)
            conversations.pop(num, None)
            send_message(GUIDE_PHONE, f'✅ Бот отключён для +{num}. Ты можешь ответить лично.')
        return True
    # /on +79261234567
    if t.startswith('/on'):
        parts = t.split()
        if len(parts) >= 2:
            num = parts[1].lstrip('+')
            activate(num)
            send_message(GUIDE_PHONE, f'✅ Бот включён для +{num}.')
        return True
    # /list — список активных диалогов
    if t == '/list':
        now = time.time()
        lines = [f'+{p}: {int((now-ts)//60)} мин назад' for p, ts in active_users.items()]
        msg = '📋 Активные диалоги:\n' + ('\n'.join(lines) if lines else 'нет')
        send_message(GUIDE_PHONE, msg)
        return True
    return False

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

            # Удаляем из очереди СРАЗУ — до обработки, чтобы не было дублей при редеплое
            if receipt_id:
                requests.delete(f'{BASE_URL}/deleteNotification/{TOKEN}/{receipt_id}', timeout=5)

            if type_ == 'incomingMessageReceived':
                msg_data = body.get('messageData', {})
                text = (msg_data.get('textMessageData', {}).get('textMessage', '') or
                        msg_data.get('extendedTextMessageData', {}).get('text', ''))
                sender = body.get('senderData', {}).get('sender', '')
                name   = body.get('senderData', {}).get('senderName', 'Гость')
                phone  = sender.replace('@c.us', '')

                if receipt_id not in processed_ids and text:
                    processed_ids.add(receipt_id)
                    stats['received'] += 1
                    print(f'[{name}] {text}')

                    # Команды от Тимура
                    if phone == GUIDE_PHONE:
                        handle_guide_command(text)
                        continue

                    trigger = is_site_trigger(text)
                    already_active = is_active(phone)

                    if trigger:
                        activate(phone)

                    if trigger or already_active:
                        activate(phone)  # обновляем timestamp
                        reply = get_ai_reply(phone, text)
                        if reply:
                            time.sleep(1.5)
                            send_message(phone, reply)
                            stats['replied'] += 1
                            print(f'→ AI: {reply[:60]}...')

                    # Тимуру — всегда (личные тоже, но помечаем)
                    tag = '' if (trigger or already_active) else '👤 '
                    send_message(GUIDE_PHONE, f'{tag}📩 *{name}* (+{phone}):\n{text}')
                    stats['forwarded'] += 1

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
        'version': 'v8',
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
