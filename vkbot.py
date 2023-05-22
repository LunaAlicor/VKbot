import concurrent.futures
import vk_api
import aiohttp
import openai
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import time
from vktoken import VKTOKEN
from openaikey import openai_key


def send_message(id: int, text: str) -> None:
    """
    Функция отправки сообщения в беседу или чат

    Входные данные:
    id (int) - идентификатор беседы
    text (str) - текст для отправки

    Результат работы:
    Функция отправляет указанный текст в беседу с указанным идентификатором
    """
    vk_session.method('messages.send', {'chat_id': id, 'message': text, 'random_id': 0})


def sen_message_private(user_id: int, text: str) -> None:
    """
    Функция отправки сообщения в личные сообщения

    Входные данные:
    user_id (int) - идентификатор пользователя
    text (str) - текст для отправки

    Результат работы:
    Функция отправляет указанный текст в личные сообщения
    """
    vk_session.method('messages.send', {'user_id': user_id, 'message': text, 'random_id': 0})


def generate_response(message_dict):
    """
       Функция для генерации ответа на основе входного сообщения

       Входные данные:
       message_dict (dict) - словарь с сообщениями для модели OpenAI

       Результат работы:
       Функция отправляет входной словарь сообщений в модель gpt-3.5-turbo и возвращает сгенерированный ответ.

       Пример использования:
       >>> message_dict = [
               {"role": "system", "content": "You are a helpful assistant."},
               {"role": "user", "content": "What's the weather like today?"}
           ]
       >>> generate_response(message_dict)
       'The weather today is sunny with a temperature of 25 degrees Celsius.'

       Примечания:
       - Для использования данной функции необходимо иметь доступ к API модели OpenAI GPT-3.5-turbo.
       - Предоставляемый входной словарь message_dict должен соответствовать требуемому формату для модели.
       - Возвращаемое значение - сгенерированный ответ на основе входных сообщений.

       """

    # Вызов API модели OpenAI для генерации ответа
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_dict
    )
    # Получение сгенерированного ответа из результата API
    return completion.choices[0].message.content.strip()


if __name__ == '__main__':

    TOKEN = VKTOKEN  # Иморт вашего токена из файла vktoken.py
    openai.api_key = openai_key  # Импорт вашего ключа openai из файла openaikey.py
    bot_group_ip = 219295386  # Укажите id вашего бота вместо id моего бота
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, bot_group_ip)
    history_dict = {}
    message_time_dict = {}


    def event_worker(event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.from_chat:  # Обработка запроса из чата
                chat_id = event.chat_id
                message = event.message
                msg = event.object.message['text'].lower()
                text = msg
                user_id = message['from_id']

                if msg.startswith('/'):  # Проверка начинается ли сообщение на специальный символ для обращения к боту
                    if user_id not in history_dict or time.time() - message_time_dict[user_id] > 180 or msg.startswith(
                            '//'):
                        history_dict[user_id] = []
                    try:
                        history_dict[user_id].append({"role": "user", "content": msg.lstrip("/")})
                        result = generate_response(message_dict=history_dict[user_id])
                        print(history_dict[user_id])
                        history_dict[user_id].append({"role": "assistant", "content": result})
                        send_message(chat_id, text=result)
                        message_time_dict[user_id] = time.time()

                        print(message_time_dict)
                    except:
                        send_message(chat_id, text='Произошла ошибка, повторите запрос.')

            else:  # Обработка запроса в личных сообщениях
                message = event.message
                msg = event.object.message['text'].lower()
                user_id = message['from_id']
                print(user_id)
                print(msg)
                if user_id not in history_dict or time.time() - message_time_dict[user_id] > 180 or msg.startswith(
                        '//'):
                    history_dict[user_id] = []
                try:
                    history_dict[user_id].append({"role": "user", "content": msg.lstrip("/")})
                    result = generate_response(message_dict=history_dict[user_id])
                    print(history_dict[user_id])
                    history_dict[user_id].append({"role": "assistant", "content": result})
                    sen_message_private(user_id, text=result)
                    message_time_dict[user_id] = time.time()

                    print(message_time_dict)
                except:
                    sen_message_private(user_id, text='Произошла ошибка, повторите запрос.')


    while True:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

                for event in longpoll.listen():
                    executor.submit(event_worker, event)
        except Exception:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

                for event in longpoll.listen():
                    executor.submit(event_worker, event)
