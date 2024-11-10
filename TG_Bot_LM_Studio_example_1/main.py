import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

# Замените 'YOUR_BOT_TOKEN' на ваш токен от BotFather
API_TOKEN = '7508304212:AAH_a3pfaKSnj_kzCkeiYCvPA3DbfP7bzu8'
bot = telebot.TeleBot(API_TOKEN)

#Тут будет храниться контекст
user_contexts = {}

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id
    if user_id in user_contexts:
        user_contexts.pop(user_id)
        bot.reply_to(message, "Контекст очищен.")
    else:
        bot.reply_to(message, "Контекст уже пуст.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    if user_id not in user_contexts:
        user_contexts[user_id] = []

    user_contexts[user_id].append({"role": "user", "content": user_query})

    request = {
        "messages": user_contexts[user_id]
    }

    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)

        reply_content = model_response.choices[0].message.content
        user_contexts[user_id].append({"role": "assistant", "content": reply_content})

        bot.reply_to(message, model_response.choices[0].message.content)
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)