import requests
import telebot #manage telegram API
import time
from telebot.types import ReplyKeyboardMarkup # add bottons 
from telebot.types import ForceReply # reply a message
from telebot.types import ReplyKeyboardRemove #remove bottons
from typing import Dict, List


BOT_TOKEN = 'YOUR_TOKEN'
API_KEY = 'YOUR_API_KEY'
BASE_URL = "https://banking.sandbox.prometeoapi.com"
data = {}
params = {}
params_2 = {}


class Authentication:
    def login(self) -> Dict:
        url = f"{BASE_URL}/login/"
        headers = {
            "X-API-Key": API_KEY
        }
        response = requests.post(url, data=data, headers=headers)
        if response.ok:
            return response.json()

    def get_session_key(self) -> str:
        login_data: Dict = self.login()
        return login_data.get("key")       


prometeo_auth = Authentication()

# instance of telegram bot
bot = telebot.TeleBot(BOT_TOKEN)

# start and help command handler
@bot.message_handler(commands=['start'])
def cmd_start(message):
    bot.send_message(message.chat.id, "Welcome to Prometeo Bot!")
    # commands
    bot.send_message(message.chat.id, "Use /login to begin your authentication")

# AUTHENTICATION

# login command handler
@bot.message_handler(commands=['login'])
def cmd_login(message):
    markup = ReplyKeyboardMarkup(one_time_keyboard= True, input_field_placeholder="Please, select an option", resize_keyboard=True)
    markup.add("test")
    msg = bot.send_message(message.chat.id, "Please, select a provider", reply_markup=markup)
    bot.register_next_step_handler(msg, get_username)

def get_username(message):
    data["provider"] = message.text
    markup = ReplyKeyboardRemove()
    msg = bot.send_message(message.chat.id, "Great! Now enter your username", reply_markup=markup)
    bot.register_next_step_handler(msg, get_password)

def get_password(message):
    data["username"] = message.text
    msg = bot.send_message(message.chat.id, "And last but not least, your password... 👀")
    bot.register_next_step_handler(msg, info_validation)


def info_validation(message):
    data["password"] = message.text
    time.sleep(0)
    bot.delete_message(message.chat.id, message.message_id)

    url = f"{BASE_URL}/login/"
    headers = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded",
    "X-API-Key": API_KEY
    }
    response = requests.post(url, data=data, headers=headers)
    print(response.text)

    if response.ok:
        msg = bot.send_message(message.chat.id, "We're validating your info...")
        msg = bot.send_message(message.chat.id, "You're now logged in 🔥")
        msg = bot.send_message(message.chat.id, """
        Now you can use these commands to move throughout your account:
        /logout to finish the session
        /accounts to check your accounts
        /account_movements to see the account movements
        /credit_cards to check your credit cards
        /cc_movements to see the credit card movements
        /providers to check the providers list
        /help to see all the available commands
        """)
    else:
        msg = bot.send_message(message.chat.id, "Ooooooops! Looks like something went wrong")
        msg = bot.send_message(message.chat.id, "Don't worry, you can try again using /login")



# logout command handler
@bot.message_handler(commands=['logout'])
def cmd_logout(message):
    session_key: str = prometeo_auth.get_session_key()

    url = f"{BASE_URL}/logout/"
    params = {
    "key": session_key
    }
    headers = {
    "X-API-Key": API_KEY
     }
    response = requests.get(url, params=params, headers=headers)

    if session_key == None:
        bot.send_message(message.chat.id, "You have already logged out")
    elif response.ok:
        print(response.json())
        session_key = None
        bot.send_message(message.chat.id, "Succesfully logged out")

# TRANSACTIONAL DATA

# accounts command handler: shows the user's accounts info
@bot.message_handler(commands=['accounts'])
def cmd_accounts(message):
    session_key: str = prometeo_auth.get_session_key()

    url = f"{BASE_URL}/account/"
    params = {
    "key": session_key
    }
    headers = {
    "X-API-Key": API_KEY
     }

    response = requests.get(url, params=params, headers=headers)
    
    accounts = response.json().get("accounts", [])
    for account in accounts:
        id = account.get('id')
        name = account.get('name')
        number = account.get('number')
        currency = account.get('currency')
        balance = account.get('balance')
        bot.send_message(message.chat.id, f"ID: {id}\nName: {name}\nNumber: {number}\nCurrency: {currency}\nBalance: {balance}")


# account_movements command handler: list the movements of an specific account in a range of date
@bot.message_handler(commands=['account_movements'])
def cmd_account_movements(message):
    markup = ForceReply()
    markup = ReplyKeyboardMarkup(one_time_keyboard= True, input_field_placeholder="Please, select an option", resize_keyboard=True)
    markup.add("Test Account 1", "Test Account 2")
    msg = bot.send_message(message.chat.id, "Please, select an account", reply_markup=markup)
    bot.register_next_step_handler(msg, get_currency)


def get_currency(message):
    if message.text == "Test Account 1":
        params["account_number"] = 12345678
    elif message.text == "Test Account 2":
        params["account_number"] = 87654321
    else:
        msg = bot.send_message(message.chat.id, "Please select a valid account")

    markup = ReplyKeyboardMarkup(one_time_keyboard= True, input_field_placeholder="Please, select an option", resize_keyboard=True)
    markup.add("UYU", "USD")
    msg = bot.send_message(message.chat.id, "Please, select the currency of the account", reply_markup=markup)
    bot.register_next_step_handler(msg, get_date_start)

def get_date_start(message):
    markup = ReplyKeyboardRemove()

    if message.text == "UYU":
        params["currency"] = "UYU"
    elif message.text == "USD":
        params["currency"] = "USD"
    else:
        msg = bot.send_message(message.chat.id, "Please select a valid currency")
    

    msg = bot.send_message(message.chat.id, "Please, enter a start date in the next pattern: dd/mm/yyyy", reply_markup=markup)
    bot.register_next_step_handler(msg, get_date_end)

def get_date_end(message):
    params["date_start"] = message.text

    msg = bot.send_message(message.chat.id, "Please, enter an end date in the next pattern: dd/mm/yyyy")
    bot.register_next_step_handler(msg, get_movements)

def get_movements(message):
    
    params["date_end"] = message.text
    session_key: str = prometeo_auth.get_session_key()
    params["key"] = session_key

    url = f"{BASE_URL}/account/{params['account_number']}/movement/"

    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
        }
    response = requests.get(url, params=params, headers=headers)
    
    movements = response.json().get("movements", [])
    for movement in movements:
        id = movement.get('id')
        reference = movement.get('reference')
        date = movement.get('date')
        detail = movement.get('detail')
        debit = movement.get('debit')
        credit = movement.get('credit')
        bot.send_message(message.chat.id, f"ID: {id}\nReference: {reference}\nDate: {date}\nDetail: {detail}\nDebit: {debit}\nCredit: {credit}")


# credit_cards command habdler: shows the user's credit cards info
@bot.message_handler(commands=['credit_cards'])
def cmd_credit_cards(message):
    session_key: str = prometeo_auth.get_session_key()

    url = f"{BASE_URL}/credit-card/"
    params = {
    "key": session_key
    }
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
     }

    response = requests.get(url, params=params, headers=headers)
    
    ccs = response.json().get("credit_cards", [])
    for cc in ccs:
        id = cc.get('id')
        name = cc.get('name')
        number = cc.get('number')
        close_date = cc.get('close_date')
        due_date = cc.get('due_date')
        balance_local = cc.get('balance_local')
        balance_dollar = cc.get('balance_dollar')
        bot.send_message(message.chat.id, f"ID: {id}\nName: {name}\nNumber: {number}\nClose date: {close_date}\nDue date: {due_date}\nBalance local: {balance_local}\nBalance dollar: {balance_dollar}")


# cc_movements command handler: list the movements of an specific credit card in a range of date
@bot.message_handler(commands=['cc_movements'])
def cmd_cc_movements(message):

    markup = ForceReply()
    markup = ReplyKeyboardMarkup(one_time_keyboard= True, input_field_placeholder="Please, select an option", resize_keyboard=True)
    markup.add("Test Credit Card")
    msg = bot.send_message(message.chat.id, "Please, select a credit card", reply_markup=markup)
    bot.register_next_step_handler(msg, get_cc_currency)


def get_cc_currency(message):
    if message.text == "Test Credit Card":
        params_2["card_number"] = "************1791"
    else:
        msg = bot.send_message(message.chat.id, "Please select a valid credit card")

    markup = ForceReply()
    markup = ReplyKeyboardMarkup(one_time_keyboard= True, input_field_placeholder="Please, select the currency", resize_keyboard=True)
    markup.add("UYU", "USD")
    msg = bot.send_message(message.chat.id, "Please, select the currency of the credit card", reply_markup=markup)
    bot.register_next_step_handler(msg, get_cc_date_start)

def get_cc_date_start(message):
    markup = ReplyKeyboardRemove()

    if message.text == "UYU":
        params_2["currency"] = "UYU"
    elif message.text == "USD":
        params_2["currency"] = "USD"
    else:
        msg = bot.send_message(message.chat.id, "Please select a valid currency")
    

    msg = bot.send_message(message.chat.id, "Please, enter a start date in the next pattern: dd/mm/yyyy", reply_markup=markup)
    bot.register_next_step_handler(msg, get_cc_date_end)

def get_cc_date_end(message):
    params_2["date_start"] = message.text

    msg = bot.send_message(message.chat.id, "Please, enter an end date in the next pattern: dd/mm/yyyy")
    bot.register_next_step_handler(msg, get_cc_movements)

def get_cc_movements(message):
    
    params_2["date_end"] = message.text
    session_key: str = prometeo_auth.get_session_key()
    params_2["key"] = session_key

    url = f"{BASE_URL}/credit-card/{params_2['card_number']}/movements"

    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
        }
    response = requests.get(url, params=params_2, headers=headers)
    
    movements = response.json().get("movements", [])
    for movement in movements:
        id = movement.get('id')
        reference = movement.get('reference')
        date = movement.get('date')
        detail = movement.get('detail')
        debit = movement.get('debit')
        credit = movement.get('credit')
        bot.send_message(message.chat.id, f"ID: {id}\nReference: {reference}\nDate: {date}\nDetail: {detail}\nDebit: {debit}\nCredit: {credit}")

# META

# providers commnad handler: list the providers
@bot.message_handler(commands=['providers'])
def cmd_providers(message):
    session_key: str = prometeo_auth.get_session_key()

    url = f"{BASE_URL}/provider/"
    headers = {
        "accept": "application/json",
        "X-API-Key": "dXb4gBLt8ceJkaXFnw7pZthEtvnKyanJtM4KuaSq2ppLulRQoQLRrLq8sgvjNO0Q"
    }
    response = requests.get(url, headers=headers)
    providers = response.json().get("providers", [])
    for provider in providers:
        code = provider.get('code')
        name = provider.get('name')
        country = provider.get('country')
        bot.send_message(message.chat.id, f"Code: {code}\nName: {name}\nCountry: {country}")


# help command handler: shows all the commands
@bot.message_handler(commands=['help'])
def cmd_start(message):
    msg = bot.send_message(message.chat.id, """
        These are the commands you can use to move around:
        /start to initialize the bot
        /login to authenticate
        /logout to logout
        /accounts to check your accounts
        /account_movements to see the account movements
        /credit_cards to check your credit cards
        /cc_movements to see the credit card movements
        /providers to check the providers list
        /help to see this message again
        """)




if __name__ == '__main__':
    print('Initializing...')
    bot.infinity_polling()