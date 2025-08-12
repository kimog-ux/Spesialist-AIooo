import telebot 
from telebot import types 
from request import gpt_request 
from config import *  
import pickle 
import os 
from mathgenerator import mathgen 
import random 

def load_user_data(): #загрузка данных из файла
    if os.path.exists('user_data.pkl'):
        with open('user_data.pkl', 'rb') as f:
            return pickle.load(f)
    return {}

def save_user_data(data):  #выгрузка данных в файл
    with open('user_data.pkl','wb') as f:
        pickle.dump(data, f)

def is_user_registered(user_id): #проверка, что пользователь зарегистрирован
    user_data = load_user_data()
    if str(user_id) in list(user_data.keys()):
        return True
    else:
        return False

def giga(message):
    bot.send_message(message.chat.id,gpt_request(message.text))
    return

bot = telebot.TeleBot(open('api.txt').read()) #Инициализация бота
user_progres = {}
math_levels = [[1,2],[3,4],[5,6]]
questions = []

def show_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*main_menu.values())
    bot.send_message(message.from_user.id, "Выберите действие:", reply_markup=markup)

def show_questions(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*question_menu.values())
    bot.send_message(message.from_user.id, "Выберите действие:", reply_markup=markup)

def math_game(message):
    if message.text == 'Меню':#Возврат в меню по желаению пользователя
        show_menu(message)
        return
    user_id = str(message.from_user.id)
    global user_progres
    user_progres[user_id] = [0,0,'']
    markup_line = types.InlineKeyboardMarkup()
    level_math = load_user_data()[user_id]['level_math']#берём данные уровня математики
    problem, answer = mathgen.genById(math_levels[level_math][random.randint(0,len(math_levels[level_math])-1)])
    problem = problem.replace(r'\cdot','*').replace('$','')
    answer = answer.replace('$','')
    corr = random.randint(0,3)
    for i in range(4):
        _, fake = mathgen.genById(math_levels[level_math][random.randint(0,len(math_levels[level_math])-1)])
        fake = fake.replace('$','')
        btn = types.InlineKeyboardButton(
            text = f'{answer if i==corr else fake}',#если i и corr равны, пишется answer, иначе fake
            callback_data=f'math_{i}_{corr}_{problem}'
        )
        markup_line.add(btn)
    msg = bot.send_message(user_id, f'Решите пример {problem}', reply_markup=markup_line)
    user_progres[user_id][2] = msg.message_id

def lesson_selection(message):
    if message.text == 'Меню': #если пользователь нажал меню - возвращаемся
        show_menu(message)
        return
    lesson = message.text #считываем урок, который ползователь выбрал
    lesson_folder = lessons[lesson] #считываем путь к конкретной папке
    try:
        send_materials(message,lesson_folder)
        bot.send_message(message.chat.id, f'Файлы урока {lesson} успешно отправлены')
    except BaseException:
        bot.send_message(message.chat.id, 'Ошибка при отправке файлов')
    show_menu(message)

def send_materials(message, folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as file:
                bot.send_message(message.from_user.id, f"Текст урока {file.read()}")
        elif filename.endswith(('.jpg','.jpeg','.png')):
            with open(file_path, 'rb') as photo:
                bot.send_photo(message.from_user.id,photo)
        elif filename.endswith(('.mp4','.mov')):
            with open(file_path, 'rb') as video:
                bot.send_video(message.from_user.id,video)
        elif filename.endswith('.pdf'):
            with open(file_path, 'rb') as pdf:
                bot.send_document(message.from_user.id,pdf, caption='Учебный файл')
        elif filename.endswith('.mp3'):
            with open(file_path, 'rb') as audio:
                bot.send_document(message.from_user.id,audio, caption='Аудио файл')
                #можно использовать также bot.send_audio()
        
def test_mode(message):
    if message.text == 'Меню': #если пользователь нажал меню - возвращаемся
        show_menu(message)
        return
    global questions, user_progres
    user_id = str(message.from_user.id)
    user_progres[user_id] = [0,0,'']
    markup = types.ReplyKeyboardMarkup()
    markup.add('Меню')
    lesson_name = list(lessons.keys())[int(message.text)-1]
    bot.send_message(user_id, f"Начинает тест по уроку {lesson_name}",reply_markup=markup)
    try:
        questions = open('test_'+str(message.text)+'.txt','r',encoding='utf-8').readlines()
    except BaseException:
        bot.send_message(user_id,'Ошибка чтения файла')
        show_menu(message)
        return
    send_question(message, questions[user_progres[user_id][0]])

def send_question(message, question):
    markup = types.InlineKeyboardMarkup()
    parts = question.split('_')
    user_id = str(message.from_user.id)
    #Сколько будет 2+2?_1_2_3_4_3
    #В переменной parts получим список ['Сколько..','1','2','3','4','3']
    for i, answer in enumerate(parts[1:-1]):
        btn = types.InlineKeyboardButton(
            text = answer,
            callback_data=f'answer_{user_progres[user_id][0]}_{i}_{parts[-1]}'
        )
        markup.add(btn)
    msg = bot.send_message(user_id, f'{user_progres[user_id][0]+1}. Вопрос {parts[0]}',reply_markup=markup)
    user_progres[user_id][2] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer(message):
    _,ques,answ,corr = message.data.split('_')
    user_id = str(message.from_user.id)
    bot.edit_message_text(
        chat_id=user_id,
        message_id=user_progres[user_id][2],
        text=f'{ques} \nНомер ответа - {int(answ)+1}',
        reply_markup=None
    )
    user_progres[user_id][0]+=1
    if int(answ) == int(corr):
        user_progres[user_id][1]+=1
    if user_progres[user_id][0] != len(questions):
        bot.send_message(user_id, 'Следующий вопрос')
        send_question(message, questions[user_progres[user_id][0]])
    else:
        bot.send_message(user_id, 'Тест завершён!')
        bot.send_message(user_id, f'Ты правильно ответил на {user_progres[user_id][1]}'
                         f' из {len(questions)} вопросов')
        user_data = load_user_data()
        score = round(user_progres[user_id][1]*100/len(questions),2)
        if score >= 60:
            user_data[user_id]['level']+=1
            bot.send_message(user_id, 'Вы прошли тест по этому модулю')
        else:
            bot.send_message(user_id, 'Вы не прошли тест, попробуйте снова')
        save_user_data(user_data)
        show_menu(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('math_'))
#срабатывает когда пользователь отправляет ответ на мат. пример
def math_answer(message):
    _,answ,corr,problem = message.data.split('_')
    user_id = str(message.from_user.id)
    bot.edit_message_text(
        chat_id=user_id,
        message_id=user_progres[user_id][2],
        text=f'Пример {problem}, ваш ответ №{answ}',
        reply_markup=None
    )
    user_data = load_user_data()
    user_id = str(message.from_user.id)
    if corr==answ:
        user_data[user_id]['score_math']+=1
        if user_data[user_id]['score_math']>=5:
            if user_data[user_id]['level_math'] <2:
                user_data[user_id]['level_math']+=1 
            user_data[user_id]['score_math']=0
        save_user_data(user_data)
        bot.send_message(user_id,'Верно!')
    else:
        bot.send_message(user_id,'Неверно!')
    msg = bot.send_message(user_id,f'Начать снова? Ваши очки - {user_data[user_id]["score_math"]}'
                           f', ваш уровень - {user_data[user_id]["level_math"]}')
                          
    bot.register_next_step_handler(msg, math_game)

@bot.message_handler(commands=['start'])
def send_wecome(message):
    bot.reply_to(message, "Привет! Я твой учебный бот!")
    if is_user_registered(message.from_user.id):
        bot.send_message(message.chat.id, 'Зарегистрирован')
        show_menu(message)
    else:
        bot.send_message(message.chat.id, 'Не зарегистрирован')
        Register_menu(message)
        
@bot.message_handler(commands=['register'])
def Register_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_phone = types.KeyboardButton('Отправить номер телефона', request_contact=True)
    markup.add(btn_phone)
    bot.send_message(message.chat.id, 'Просьба пройти регистрацию.\n\n' 
                     '1. Нажмите на кнопку, чтобы отправить номер телефон\n'
                     '2. Затем введите ФИО', reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
   user_id = str(message.from_user.id)#получение ID пользователя
   phone = message.contact.phone_number #получаем номер телефона из сообщения, которое отправили
   user_data = load_user_data() #загружаем информацию о пользователях, которая уже есть
   if user_id not in user_data: #проверяем, что пользователя с таким ID нет
       user_data[user_id] = {} #если его нет, то добавляем в список пользователей
   user_data[user_id]['phone'] = phone #по ID пользователя добавляем поле номер телефона
   user_data[user_id]['level_math'] = 0  # Уровень в математике
   user_data[user_id]['score_math'] = 0  # Счет в математике
   user_data[user_id]['level'] = 0 #уровень урока, который пройден
   save_user_data(user_data) #сохраняем в файл полученную информацию
   bot.send_message(message.chat.id,'Вы зарегистрированы')
   show_menu(message)

@bot.message_handler(func=lambda message:True)
def handle_buttons(message):
    if message.text == 'Расписание':
        bot.reply_to(message, "Сейчас каникулы, расписание будет после 1 сентября.")
        inline_markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(
            text="Летние активности",
            url="https://leto.mos.ru/"
        )
        inline_markup.add(btn)
        bot.send_message(message.chat.id, "Лучше посмотри летние активности",
                         reply_markup=inline_markup)
        
    elif message.text == 'Информация о школе':
        bot.reply_to(message, "Информация обновляется.")
        inline_markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(
            text="Актуальная информация",
            url="https://sch338tn.mskobr.ru/"
        )
        inline_markup.add(btn)
        bot.send_message(message.chat.id, "Вся информация в прикрепленной ссылке",
                         reply_markup=inline_markup)
        
    elif message.text == "Домашнее задание":
        bot.reply_to(message, "Обрати внимание на рекомендованный список литературы.")
        inline_markup = types.InlineKeyboardMarkup()  
        doc = open('Список литературы.pdf','rb')
        bot.send_document(message.chat.id, doc,caption='Домашнее задание',
                          visible_file_name='Список литературы.pdf')

    elif message.text == "Успеваемость":
        bot.reply_to(message, "Авторизируйся в МЭШ.")
        inline_markup = types.InlineKeyboardMarkup() 
    
    elif message.text == "Звонки":
        bot.reply_to(message, "Расписание звонков на 2025 г.")
        ph = open('Расписание звонков.jpg', 'rb')
        bot.send_photo(message.chat.id,ph,'Звонки')
        url = 'https://polinka.top/pics1/uploads/posts/2023-11/thumbs/1700233018_polinka-top-p-kartinka-budni-uchitelya-4.jpg'
        bot.send_photo(message.chat.id,url,'Звонки')

    elif str(message.text).lower() == 'привет':
        bot.reply_to(message, "Привет!")

    elif message.text == 'Фото':
        try:
            ph = open('name_file.jpg','rb')
            bot.send_photo(message.chat.id,ph,'Ваше последнее фото')
        except BaseException:
            bot.reply_to(message, "Фото отсутствует, отправьте новое.")

    elif message.text == 'Вопрос GigaChat':
        msg = bot.reply_to(message, "Задай вопрос")
        bot.register_next_step_handler(msg, giga)

    elif message.text == 'Общие вопросы.':
        bot.reply_to(message, "Вы попали в раздел ответов на вопросы, выберите один из вопросов")
        show_questions(message)
    
    elif message.text == 'Игра в математику':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Меню", "Начать!")
        msg = bot.send_message(
            message.chat.id,
            "Добро пожаловать в математический квиз\nнажмите начать",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, math_game)

    elif message.text == "Начать обучение":
        user_data = load_user_data()
        user_id = str(message.from_user.id)
        level = user_data[user_id]['level']#временно поставим зависимость от уровня математики
        level = 4
        #если хотите посмотреть все уроки, временно напишите level = 4
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Меню')
        avalible_lessons = list(lessons.keys())[0:level+1]#при таком обрезании списка - [0,2)
        for lesson in avalible_lessons:
            markup.add(types.KeyboardButton(lesson))
        msg = bot.send_message(user_id, 'Выберите урок для изучения', 
                               reply_markup=markup)
        bot.register_next_step_handler(msg,lesson_selection)
    elif message.text == 'Начать тестирование':
        user_data = load_user_data()
        user_id = str(message.from_user.id)
        level = user_data[user_id]['level']
        markup = types.ReplyKeyboardMarkup()
        for i in range(level+1):
            markup.add(f'{i+1}')
        markup.add('Меню')
        msg = bot.send_message(user_id,"Выберите тест для прохождения",
                               reply_markup=markup)
        bot.register_next_step_handler(msg, test_mode)
        
@bot.message_handler(content_types=['photo'])
def photoes(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    download_file = bot.download_file(file_info.file_path)
    with open('name_file.jpg', 'wb') as new_f:
        new_f.write(download_file)
    bot.reply_to(message,'Фото сохранено')


    
bot.polling()        
    
  
   
