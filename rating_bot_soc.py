import datetime
import logging
import os
import re
import uuid

# from datetime import datetime
import psycopg2
import pytz
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from timezonefinder import TimezoneFinder

load_dotenv()

dbname = os.getenv("DBNAME")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")


try:
    connection = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    cursor = connection.cursor()
    print("Подключение к базе данных успешно!")


except (Exception, psycopg2.Error) as error:
    print("Ошибка при подключении к базе данных PostgreSQL:", error)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

(
    CHOOSE_OPTION,
    REGISTRATION_INFO,
    ADD_TASK,
    ROLE,
    CITY,
    COMENTS,
    LIKES,
    REPOSTS,
    CHOOSE_TYPE,
    SKILLS,
    FOLLOWS,
    USER_NAME,
) = range(12)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    create_table_query = """CREATE TABLE IF NOT EXISTS registr
                         (id SERIAL PRIMARY KEY,
                          linkedURL VARCHAR(2000),
                          city VARCHAR(50),
                          time_zone VARCHAR(100),
                          role VARCHAR(200),
                          status INTEGER DEFAULT 0,
                          engage_rate INTEGER);"""
    cursor.execute(create_table_query)
    connection.commit()
    cursor.execute(
        """INSERT INTO registr (id) VALUES (%s) ON CONFLICT (id) DO NOTHING""",
        (update.effective_user.id,),
    )
    connection.commit()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""
Welcome to the LinkedIn co-boosting service. Our community is built on the contribute-to-get principle.
This means that you need to complete tasks from other participants in order for your tasks to be completed.
The higher your ratio of completed tasks to assigned tasks, the higher your rating and the greater the chance of your task being accomplished.
Task completion is based on mutual trust. We believe that by marking a task as completed, you are telling the truth.
We perform random checks on task completion. Deception will result in a lifetime ban. If you agree with these principles, simply register with the bot by following the instructions.
Good luck with enhancing your LinkedIn profile.""",
    )
    return await midle_option(update, context)


async def midle_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    user_id = update.effective_user.id
    select_query = """SELECT linkedURL FROM registr WHERE id = %s;"""
    cursor.execute(select_query, (user_id,))
    rows = cursor.fetchall()
    if rows and rows[0][0] is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Insert your LinkedIn profile URL. It sholud be like this one https://www.linkedin.com/in/leonidgladilin/",
        )
        return REGISTRATION_INFO
    else:
        return await menu(update, context)


async def reg_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    pattern = r"^https?://(www\.)?linkedin\.com/.*$"
    url = update.effective_message.text
    if re.match(pattern, url):
        insert_query = """UPDATE registr SET linkedURL = %s WHERE id = %s;"""
        new_user = url
        cursor.execute(
            insert_query,
            (
                new_user,
                update.effective_user.id,
            ),
        )
        connection.commit()
        current_time = datetime.datetime.now()
        update_query = """UPDATE registr SET creat_time = %s WHERE id = %s;"""
        cursor.execute(
            update_query,
            (
                current_time,
                update.effective_user.id,
            ),
        )
        connection.commit()
        update_query_name = """UPDATE registr SET user_name = %s WHERE id = %s;"""
        cursor.execute(
            update_query_name,
            (
                update.effective_user.full_name,
                update.effective_user.id,
            ),
        )
        connection.commit()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="""Add your name exactly like on LinkedIn""",
        )
        return USER_NAME
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You have entered the incorrect URL. Make sure that you paste full LinkedIn URL from your browser",
        )
        return await midle_option(update, context)


async def user_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    user_name = update.effective_message.text
    insert_query = """UPDATE registr SET linkedin_name = %s WHERE id = %s;"""
    new_user = user_name
    cursor.execute(
        insert_query,
        (
            new_user,
            update.effective_user.id,
        ),
    )
    connection.commit()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Name your Profession (SEO specialist, PPC specialist, Head of e-commerce, etc)",
    )
    return ROLE


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    city = update.effective_message.text
    insert_query = """UPDATE registr SET city = %s WHERE id = %s;"""
    new_user = city
    cursor.execute(
        insert_query,
        (
            new_user,
            update.effective_user.id,
        ),
    )
    connection.commit()
    return await time_zone(update, context)


async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    role = update.effective_message.text
    insert_query = """UPDATE registr SET role = %s WHERE id = %s;"""
    new_user = role
    cursor.execute(
        insert_query,
        (
            new_user,
            update.effective_user.id,
        ),
    )
    connection.commit()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter your city name. If we can't match the city, please enter your country's capital name. It helps us not to notify you at night.",
    )
    return CITY


async def time_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    select_query = """SELECT city FROM registr WHERE id = %s;"""
    cursor.execute(select_query, (update.effective_user.id,))
    city = cursor.fetchone()[0]
    geo = Nominatim(user_agent="SuperMon_Bot")
    location = geo.geocode(city, language="eng")
    if location is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I'm sorry, I can't find the city. Please, enter your country's capital name.",
        )
        return CITY
    else:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        tz = pytz.timezone(timezone_str)
        tz_info = datetime.datetime.now(tz=tz).strftime("%z")
        tz_info = tz_info[0:3] + ":" + tz_info[3:]  # приводим к формату ±ЧЧ:ММ
        insert_query = """UPDATE registr SET time_zone = %s WHERE id = %s;"""
        new_user = timezone_str
        cursor.execute(
            insert_query,
            (
                new_user,
                update.effective_user.id,
            ),
        )
        connection.commit()
        return await menu(update, context)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Add your task", "Take new task"]]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You have successfully signed up. Now you can use the service. Good luck",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=True
        ),
    )
    return CHOOSE_OPTION


async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    if update.effective_message.text == "Add your task":
        cursor.execute(
            """SELECT status FROM registr WHERE id = %s;""", (update.effective_user.id,)
        )
        status = cursor.fetchone()[0]
        status = int(status)
        if status == 5:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Your daily limit is over. You can add new tasks tomorrow. Thank you and have a lovely day.",
            )

            return await menu(update, context)
        else:
            return await add_task(update, context)
    elif update.effective_message.text == "Take new task":
        return await send_top5(update, context)
    elif update.effective_message.text == "✅ Done":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Great! You've completed all tasks. You can return back to the menu.",
        )
        cursor.execute(
            """UPDATE do_task SET do_status = %s WHERE task_user_id = %s;""",
            (
                "1",
                update.effective_user.id,
            ),
        )
        connection.commit()
        return await menu(update, context)


async def write_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Abort task creation and return to the menu"]]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Insert your task's LinkedIn URL.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return ADD_TASK


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        ["Like", "Follow", "Repost"],
        ["Comment", "Endorse skill"],
        ["Abort task creation and return to the menu"],
    ]
    cursor = connection.cursor()
    create_table_query = """CREATE TABLE IF NOT EXISTS add_task
                         (task_id UUID PRIMARY KEY,
                          task_type VARCHAR(100),
                          linked_url VARCHAR(2000),
                          many INTEGER,
                          much INTEGER,
                          rating INTEGER,
                          rate_calc_f INTEGER,
                          rate_calc_s INTEGER,
                          user_id INTEGER,
                          CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES registr(id));"""
    cursor.execute(create_table_query)
    connection.commit()
    cursor = connection.cursor()
    cursor.execute(
        """UPDATE add_task SET rating = r.engage_rate FROM registr r INNER JOIN add_task t ON r.id = t.user_id;"""
    )
    connection.commit()
    task_id = str(uuid.uuid4())
    context.user_data["task_id"] = task_id
    insert_query = """INSERT INTO add_task (task_id, user_id) VALUES (%s, %s);"""
    cursor.execute(insert_query, (task_id, update.effective_user.id))
    connection.commit()
    current_time = datetime.datetime.now()
    update_query = """UPDATE add_task SET creat_time = %s WHERE task_id = %s;"""
    cursor.execute(
        update_query,
        (
            current_time,
            task_id,
        ),
    )
    connection.commit()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please, choose task's type:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=True
        ),
    )
    return CHOOSE_TYPE


async def linked_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Add your task", "Take new task"]]
    pattern = r"^https?://(www\.)?linkedin\.com/.*$"
    url = update.effective_message.text
    task_id = context.user_data["task_id"]
    if url == "Abort task creation and return to the menu":
        delete_query = """DELETE FROM add_task WHERE task_id = %s;"""
        cursor.execute(delete_query, (task_id,))
        connection.commit()
        cursor.execute(
            """UPDATE add_task SET task_id = NULL WHERE task_id = %s;""", (task_id,)
        )
        connection.commit()
        return await menu(update, context)
    else:
        if re.match(pattern, url):
            insert_query = """UPDATE add_task SET linked_url = %s WHERE task_id = %s;"""
            new_task = url
            cursor.execute(
                insert_query,
                (
                    new_task,
                    task_id,
                ),
            )
            connection.commit()
            cursor.execute(
                """SELECT status FROM registr WHERE id = %s;""",
                (update.effective_user.id,),
            )
            status = cursor.fetchone()[0]
            status = int(status)
            status += 1
            insert_query2 = """UPDATE registr SET status = %s WHERE id = %s;"""
            new_task2 = status
            cursor.execute(
                insert_query2,
                (
                    new_task2,
                    update.effective_user.id,
                ),
            )
            connection.commit()
            select = """SELECT linkedin_name FROM registr WHERE id = %s;"""
            cursor.execute(select, (update.effective_user.id,))
            name = cursor.fetchone()[0]
            insert_query = """UPDATE add_task SET user_name = %s WHERE task_id = %s;"""
            new_task = name
            cursor.execute(insert_query, (new_task, task_id))
            connection.commit()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Great! You've added a new task. What do you prefer to do next?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, resize_keyboard=True, one_time_keyboard=True
                ),
            )
            return CHOOSE_OPTION
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Incorrect URL. Please, make sure that you paste correct and full LinkedIn URL to your task",
            )
            return await write_function(update, context)


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    task_id = context.user_data["task_id"]
    if update.effective_message.text == "Follow":
        insert_query0 = """UPDATE add_task SET task_type = %s WHERE task_id = %s;"""
        new_task0 = "Follow 👋"
        cursor.execute(insert_query0, (new_task0, task_id))
        connection.commit()
        return await many_follows_text(update, context)
    elif update.effective_message.text == "Endorse skill":
        insert_query5 = """UPDATE add_task SET task_type = %s WHERE task_id = %s;"""
        new = "Endorse skill 🎓"
        cursor.execute(insert_query5, (new, task_id))
        connection.commit()
        return await many_skills_text(update, context)
    elif update.effective_message.text == "Like":
        insert_query1 = """UPDATE add_task SET task_type = %s WHERE task_id = %s;"""
        new_task = "Like 👍"
        cursor.execute(insert_query1, (new_task, task_id))
        connection.commit()
        return await many_likes_text(update, context)
    elif update.effective_message.text == "Comment":
        insert_query2 = """UPDATE add_task SET task_type = %s WHERE task_id = %s;"""
        new_task_2 = "Comment 💬"
        cursor.execute(insert_query2, (new_task_2, task_id))
        connection.commit()
        return await many_coments_text(update, context)
    elif update.effective_message.text == "Repost":
        insert_query3 = """UPDATE add_task SET task_type = %s WHERE task_id = %s;"""
        new_task_3 = "Repost ♻️"
        cursor.execute(insert_query3, (new_task_3, task_id))
        connection.commit()
        return await many_reposts_text(update, context)
    elif update.effective_message.text == "Abort task creation and return to the menu":
        return await menu(update, context)
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, you should choose type of your task from reply keyboard, don't type anything by yourself please!",
        )
        return await add_task(update, context)


async def many_likes_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="How many likes do you need for the post? (10 is max)",
    )
    return LIKES


async def many_coments_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="How many comments do you need for the post? (2 is max)",
    )
    return COMENTS


async def many_reposts_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="How many reposts do you need for the post? (3 is max)",
    )
    return REPOSTS


async def many_follows_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="How many follower do you need for your profile? (5 is max)",
    )
    return FOLLOWS


async def many_skills_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="How many endorses do you need to get? (1 is max)",
    )
    return SKILLS


async def many_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    endorse = update.effective_message.text
    try:
        endorse = int(update.effective_message.text)
        task_id = context.user_data["task_id"]
        if endorse == 1:
            insert_query = """UPDATE add_task SET many = %s WHERE task_id = %s;"""
            new_task = endorse
            cursor.execute(insert_query, (new_task, task_id))
            connection.commit()
            insert_query2 = (
                """UPDATE add_task SET rate_calc_f = %s WHERE task_id = %s;"""
            )
            new_rate = 160
            new_rate = new_rate
            cursor.execute(insert_query2, (new_rate, task_id))
            connection.commit()
            insert_query3 = (
                """UPDATE add_task SET rate_calc_s = %s WHERE task_id = %s;"""
            )
            new_rate2 = 1 / endorse
            new = new_rate2
            cursor.execute(insert_query3, (new, task_id))
            connection.commit()
            return await write_function(update, context)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You can't enter more than one endorsement",
            )
            return await many_skills_text(update, context)
    except:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please adjust the number you entered to fit within the limits. The current number you entered exceeds the acceptable range. Thank you.",
        )
        return await many_skills_text(update, context)


async def many_follows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    try:
        follow = int(update.effective_message.text)
        task_id = context.user_data["task_id"]
        if follow <= 5 and follow > 0:
            insert_query = """UPDATE add_task SET many = %s WHERE task_id = %s;"""
            new_task = follow
            cursor.execute(insert_query, (new_task, task_id))
            connection.commit()
            insert_query2 = (
                """UPDATE add_task SET rate_calc_f = %s WHERE task_id = %s;"""
            )
            new_rate = 170
            new_rate = new_rate
            cursor.execute(insert_query2, (new_rate, task_id))
            connection.commit()
            insert_query3 = (
                """UPDATE add_task SET rate_calc_s = %s WHERE task_id = %s;"""
            )
            new_rate2 = 5 / follow
            new = new_rate2
            cursor.execute(insert_query3, (new, task_id))
            connection.commit()
            return await write_function(update, context)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="5 is a limit per the 'followers' task",
            )
            return await many_follows_text(update, context)
    except:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please adjust the number you entered to fit within the limits. The current number you entered exceeds the acceptable range. Thank you.",
        )
        return await many_follows_text(update, context)


async def many_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    try:
        likes = int(update.effective_message.text)
        task_id = context.user_data["task_id"]
        if likes <= 10 and likes > 0:
            insert_query = """UPDATE add_task SET many = %s WHERE task_id = %s;"""
            new_task = likes
            cursor.execute(insert_query, (new_task, task_id))
            connection.commit()
            insert_query2 = (
                """UPDATE add_task SET rate_calc_f = %s WHERE task_id = %s;"""
            )
            new_rate = 100
            new_rate = new_rate
            cursor.execute(insert_query2, (new_rate, task_id))
            connection.commit()
            insert_query3 = (
                """UPDATE add_task SET rate_calc_s = %s WHERE task_id = %s;"""
            )
            new_rate2 = 10 / likes
            new = new_rate2
            cursor.execute(insert_query3, (new, task_id))
            connection.commit()
            return await write_function(update, context)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="10 is a limit per the 'like' task",
            )
            return await many_likes_text(update, context)
    except:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please adjust the number you entered to fit within the limits. The current number you entered exceeds the acceptable range. Thank you.",
        )
        return await many_likes_text(update, context)


async def many_coments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    try:
        coments = int(update.effective_message.text)
        task_id = context.user_data["task_id"]
        if coments <= 2 and coments > 0:
            insert_query = """UPDATE add_task SET many = %s WHERE task_id = %s;"""
            new_task = coments
            cursor.execute(insert_query, (new_task, task_id))
            connection.commit()
            insert_query2 = (
                """UPDATE add_task SET rate_calc_f = %s WHERE task_id = %s;"""
            )
            new_rate = 200
            new_rate = new_rate
            cursor.execute(insert_query2, (new_rate, task_id))
            connection.commit()
            insert_query3 = (
                """UPDATE add_task SET rate_calc_s = %s WHERE task_id = %s;"""
            )
            new_rate2 = 2 / coments
            new = new_rate2
            cursor.execute(insert_query3, (new, task_id))
            connection.commit()
            return await write_function(update, context)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="2 is a limit per the 'comments' task",
            )
            return await many_coments_text(update, context)
    except:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please adjust the number you entered to fit within the limits. The current number you entered exceeds the acceptable range. Thank you.",
        )
        return await many_coments_text(update, context)


async def many_reposts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    try:
        reposts = int(update.effective_message.text)
        task_id = context.user_data["task_id"]
        if reposts <= 3 and reposts > 0:
            insert_query = """UPDATE add_task SET many = %s WHERE task_id = %s;"""
            new_task = reposts
            cursor.execute(insert_query, (new_task, task_id))
            connection.commit()
            insert_query2 = (
                """UPDATE add_task SET rate_calc_f = %s WHERE task_id = %s;"""
            )
            new_rate = 130
            new_rate = new_rate
            cursor.execute(insert_query2, (new_rate, task_id))
            connection.commit()
            insert_query3 = (
                """UPDATE add_task SET rate_calc_s = %s WHERE task_id = %s;"""
            )
            new_rate2 = 3 / reposts
            new = new_rate2
            cursor.execute(insert_query3, (new, task_id))
            connection.commit()
            return await write_function(update, context)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="3 is a limit per the 'repost' task",
            )
            return await many_reposts_text(update, context)
    except:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please adjust the number you entered to fit within the limits. The current number you entered exceeds the acceptable range. Thank you.",
        )
        return await many_reposts_text(update, context)


async def send_top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    create_table_query = """CREATE TABLE IF NOT EXISTS do_task
                         (do_task_id VARCHAR(500),
                          do_task_type VARCHAR(100),
                          do_linked_url VARCHAR(2000),
                          do_many INTEGER,
                          task_user_id BIGINT,
                          do_rating INTEGER,
                          do_status INTEGER DEFAULT 0,
                          rate_calc_f INTEGER,
                          rate_calc_s INTEGER,
                          start_time TIMESTAMP,
                          first_user_id INTEGER,
                          CONSTRAINT fk_user_id FOREIGN KEY (task_user_id) REFERENCES registr(id));"""
    cursor.execute(create_table_query)
    connection.commit()
    create_table = """
                    CREATE TABLE IF NOT EXISTS finished_tasks
                    (finished_task_id VARCHAR(500),
                     finished_task_type VARCHAR(100),
                     finished_linked_url VARCHAR(2000),
                     first_user_id INTEGER,
                     task_user_id BIGINT,
                     start_time TIMESTAMP,
                     finished_time TIMESTAMP,
                     create_id UUID);
"""
    cursor.execute(create_table)
    connection.commit()
    cursor.execute(f"""
            SELECT task_id, task_type, linked_url, many, rating, user_id, rate_calc_f, rate_calc_s, user_name
            FROM add_task
            WHERE many > 0 AND user_id != {update.effective_user.id} AND task_id NOT IN (SELECT do_task_id FROM do_task WHERE task_user_id = {update.effective_user.id})
            ORDER BY rating DESC
            LIMIT 1;
        """)

    top_tasks = cursor.fetchall()

    if top_tasks:
        total_rate = sum(rate[6] for rate in top_tasks)
        total_rate2 = sum(rate[7] for rate in top_tasks)
        revoke_coefficient = 1.1
        rank = (1 * total_rate * total_rate2) * revoke_coefficient
        for (
            task_id,
            task_type,
            linked_url,
            many,
            rating,
            user_id,
            rate_calc_f,
            rate_calc_s,
            user_name,
        ) in top_tasks:
            insert = (
                """INSERT INTO do_task (do_task_id, task_user_id) VALUES (%s, %s);"""
            )
            cursor.execute(insert, (task_id, update.effective_user.id))
            connection.commit()
            update_query = """
                UPDATE do_task 
                SET do_task_type = %s,
                    do_linked_url = %s,
                    do_many = %s,
                    do_rating = %s,
                    rate_calc_f = %s,
                    first_user_id = %s,
                    user_name = %s
                WHERE task_user_id = %s;"""
            cursor.execute(
                update_query,
                (
                    task_type,
                    linked_url,
                    many,
                    rating,
                    rank,
                    user_id,
                    user_name,
                    update.effective_user.id,
                ),
            )
            connection.commit()
            insert_query = """UPDATE do_task SET start_time = CURRENT_TIMESTAMP WHERE do_task_id = %s;"""
            cursor.execute(insert_query, (task_id,))
            connection.commit()
        if isinstance(linked_url, str):
            # Проверяем, является ли linked_url строкой и не является ли пустой строкой
            # Отправляем сообщение с ссылкой
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Here is your task. Please complete it in 15 minutes",
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"""
PLease, help *{user_name}*:
Visit this [link]({linked_url})
And *{task_type}*
                        """,
                parse_mode="Markdown",
            )
            # Отправляем запрос на подтверждение готовности выполнения задания

            return await finishing_task(update, context)
        else:
            # Отправляем сообщение о том, что нет доступных задач в базе данных
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="There are currently no available tasks in the database",
            )
            # Возвращаемся к основному меню
            return await menu(update, context)
    else:
        # Отправляем сообщение о том, что нет доступных задач в базе данных
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="There are currently no available tasks in the database",
        )
        # Возвращаемся к основному меню
        return await menu(update, context)


async def finishing_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["✅ Done"]]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You have 15 minutes to complete the task. If you skip it, your rating will be decreased.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        ),
    )
    time_delta = datetime.timedelta(minutes=1)
    context.job_queue.run_once(
        chek_chek, time_delta, chat_id=update.effective_chat.id, data=update
    )
    return CHOOSE_OPTION


async def chek_chek(context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    job = context.job
    select_query = """SELECT do_status FROM do_task WHERE task_user_id = %s;"""
    cursor.execute(select_query, (job.data.effective_user.id,))
    status = cursor.fetchone()[0]
    status = int(status)
    if status == 1:
        create_id = str(uuid.uuid4())
        insert_uqer = """INSERT INTO finished_tasks (create_id) VALUES (%s);"""
        cursor.execute(insert_uqer, (create_id,))
        connection.commit()
        cursor.execute(f"""
            SELECT rate_calc_f, do_many, do_task_id, do_task_type, do_linked_url, task_user_id, first_user_id, start_time FROM do_task WHERE task_user_id = {job.data.effective_user.id} ORDER BY start_time DESC LIMIT 5;
        """)

        for rate in cursor.fetchall():
            user_rate = rate[0]
            user_many = rate[1]
            task_id = rate[2]
            task_type = rate[3]
            liked_url = rate[4]
            task_user_id = rate[5]
            f_user_id = rate[6]
            start_time = rate[7]
            start_time = str(start_time)
            insrt = """UPDATE finished_tasks 
                    SET finished_task_id = %s,
                     finished_task_type = %s,
                     finished_linked_url = %s,
                     first_user_id = %s,
                     task_user_id = %s,
                     start_time = %s,
                     finished_time = CURRENT_TIMESTAMP 
                     WHERE create_id = %s;"""
            cursor.execute(
                insrt,
                (
                    task_id,
                    task_type,
                    liked_url,
                    f_user_id,
                    task_user_id,
                    start_time,
                    create_id,
                ),
            )
            connection.commit()
            user_many -= 1
            insert_query2 = """UPDATE add_task SET many = %s WHERE task_id = %s;"""
            cursor.execute(
                insert_query2,
                (
                    user_many,
                    task_id,
                ),
            )
            connection.commit()
            insert_query = """UPDATE registr SET engage_rate = %s WHERE id = %s;"""
            cursor.execute(
                insert_query,
                (
                    user_rate,
                    job.data.effective_user.id,
                ),
            )
            connection.commit()

    elif status == 0:
        return await pull_back(job.data, context)


async def pull_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT do_task_id, do_task_type, do_linked_url, do_many, first_user_id
        FROM do_task
        WHERE now() - start_time >= INTERVAL '15 minute' 
        AND task_user_id = {update.effective_user.id};
    """)
    unfinished_tasks = cursor.fetchall()

    for (
        do_task_id,
        do_task_type,
        do_linked_url,
        do_many,
        first_user_id,
    ) in unfinished_tasks:
        cursor.execute(
            """
            DELETE FROM do_task WHERE do_task_id = %s;
        """,
            (do_task_id,),
        )
        connection.commit()

        cursor.execute(
            """
            UPDATE add_task
            SET rating = rating * 1.1
            WHERE task_id = %s;
        """,
            (do_task_id,),
        )
        connection.commit()

        cursor.execute(
            """
            UPDATE registr
            SET engage_rate = engage_rate * 1.1
            WHERE id = %s;
        """,
            (first_user_id,),
        )
        connection.commit()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You've missed your task submission. All tasks were revoked, You can't complete new tasks till tomorrow. Your rating decreased.",
    )
    cursor = connection.cursor()
    cursor.execute(
        """UPDATE add_task SET rating = r.engage_rate FROM registr r INNER JOIN add_task t ON r.id = t.user_id;"""
    )
    connection.commit()

    return await menu(update, context)


async def clear_task_limit(context):
    cursor.execute("""SELECT id FROM registr;""")
    user_list = cursor.fetchall()
    placeholders = ",".join(["%s" for _ in user_list])
    query = f"""UPDATE registr SET status = 0 WHERE id IN ({placeholders});"""
    cursor.execute(query, user_list)


async def send_everyone(context):
    cursor.execute("""SELECT user_id, time_zone FROM registr;""")
    users = cursor.fetchall()
    for user_id, timezone_offset in users:
        utc_now = datetime.now(datetime.UTC)
        user_timezone = pytz.timezone(timezone_offset)
        user_local_time = utc_now.replace(tzinfo=pytz.utc).astimezone(user_timezone)
        if user_local_time.hour == 13:
            context.bot.send_message(
                chat_id=user_id,
                text="Hi! How is your day? Let's add some tasks to boost your profile and take some tasks to help the community.",
            )


def main():
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_OPTION: [MessageHandler(filters.TEXT, choose_option)],
            CHOOSE_TYPE: [MessageHandler(filters.TEXT, choose_type)],
            LIKES: [MessageHandler(filters.TEXT, many_likes)],
            COMENTS: [MessageHandler(filters.TEXT, many_coments)],
            REPOSTS: [MessageHandler(filters.TEXT, many_reposts)],
            ADD_TASK: [MessageHandler(filters.TEXT, linked_in)],
            CITY: [MessageHandler(filters.TEXT, city)],
            ROLE: [MessageHandler(filters.TEXT, role)],
            REGISTRATION_INFO: [MessageHandler(filters.TEXT, reg_info)],
            SKILLS: [MessageHandler(filters.TEXT, many_skills)],
            FOLLOWS: [MessageHandler(filters.TEXT, many_follows)],
            USER_NAME: [MessageHandler(filters.TEXT, user_name)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)
    application.job_queue.run_daily(
        clear_task_limit,
        datetime.time(hour=11, minute=25, tzinfo=pytz.timezone("Europe/London")),
    )
    hour_now = (datetime.datetime.now().hour + 1) % 24

    application.job_queue.run_repeating(
        send_everyone,
        datetime.timedelta(minutes=30),
        datetime.time(hour=hour_now, minute=0),
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
