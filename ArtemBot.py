import telebot
import sqlite3
from pytube import YouTube
import os
import certifi
import urllib3
import logging



# Отключаем предупреждения о небезопасных запросах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Инициализация бота с использованием токена
bot = telebot.TeleBot('6771215938:AAFTXZawoDOKt3krZODOrR2I8ePtA066IYY')

# Импорт доверенного сертификата для библиотеки requests
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

# Настройка логгирования для отладки SSL
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('urllib3')
logger.setLevel(logging.DEBUG)

# Функция для создания таблиц в базе данных, если они не существуют
def create_tables():
    connect = sqlite3.connect('bot_database.db')
    cursor = connect.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            user_links TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            youtube_link TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    connect.commit()

# Обработчик для обработки сообщений, содержащих ссылку на YouTube
def handle_video(message):
    print("Handling video message...")
    if 'youtube.com' in message.text:
        try:
            print(f"Processing YouTube link: {message.text}")
            youtube_video = YouTube(message.text)
            video_stream = youtube_video.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()

            if video_stream:
                print(f"Selected video stream: {video_stream}")
                video_path = video_stream.download('D:\\new\\bottg\\tgBotfiles\\videos')

                params = {'chat_id': message.chat.id}
                
                with open(video_path, 'rb') as video_file:
                    # Отправка видео
                    bot.send_video(message.chat.id, video_file, caption=f"Video: {youtube_video.title}", parse_mode="Markdown", timeout=60)

                connect = sqlite3.connect('bot_database.db')
                cursor = connect.cursor()

                # Создание таблиц при первом запуске бота
                create_tables()

                people_id, people_username = message.chat.id, message.chat.username
                cursor.execute(f"SELECT user_id FROM users WHERE user_id={people_id} OR username='{people_username}'")
                data = cursor.fetchone()

                if data is None:
                    user_data = [message.from_user.id, message.from_user.username]
                    cursor.execute('''
                        INSERT INTO users (user_id, username, user_links)
                        VALUES (?, ?, ?)
                    ''', (user_data[0], user_data[1], message.text))
                    connect.commit()

                # Добавляем ссылку в базу данных
                cursor.execute("INSERT INTO videos (user_id, youtube_link) VALUES (?, ?)", (message.chat.id, message.text))
                connect.commit()

                print(f"Video '{youtube_video.title}' successfully downloaded and link added to the database")
                
                # Удаление временного файла
                os.remove(video_path)
            else:
                print("Failed to find a suitable stream for downloading the video.")
                bot.send_message(message.chat.id, "Failed to find a suitable stream for downloading the video.")

        except Exception as e:
            print(f"An error occurred while downloading the video (if the video exists, there is no error): {e}")
            bot.send_message(message.chat.id, f"An error occurred while downloading the video (if the video exists, there is no error): {e}")


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command_handler(message):
    start_command(message)
    
    # Обработчик команды /delete
@bot.message_handler(commands=['delete'])
def delete_command_handler(message):
    delete_command(message)

# Обработчик для обработки сообщений, содержащих ссылку на YouTube
@bot.message_handler(func=lambda message: 'youtube.com' in message.text)
def video_command(message):
    handle_video(message)

# Запуск бота в режиме long polling
if __name__ == "__main__":
    bot.polling(none_stop=True)