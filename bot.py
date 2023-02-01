import logging
import os
import sqlite3
import re
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ApplicationBuilder, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from dotenv import load_dotenv

load_dotenv()

#load variables
bot_key = os.environ['BOT_KEY']

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

keyb = [["Portfolio", "Market"]]
reply_markup = ReplyKeyboardMarkup(keyb, resize_keyboard=True, one_time_keyboard=False)


async def start(update, context):
    tg_id = update.message.chat_id
    chat_id = update.effective_chat.id
    msg = "Welcome to <b>Endless Futures</b>\n\n"
    msg = msg + "IMPORTANT - its all virtual futures." 
    sql = sqlite3.connect('endless.db')
    db = sql.cursor()
    result = db.execute('SELECT user_id FROM users where user_id =' + str(tg_id))
    rows = result.fetchall()
    if len(rows) == 0:
        db.execute("INSERT INTO users(user_id) VALUES(?)", (str(tg_id), ))
        sql.commit()  
        db.execute("INSERT INTO balances(user_id, amount, currency) VALUES(?, ?, ?)", (str(tg_id), 1000, 'USD'))
        sql.commit()   
        msg = msg + "\n\nGift for you 1000 USD for playing\n\nEnjoy!"    
    sql.close()      
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML', reply_markup=reply_markup)        


async def help(update, context):
    msg = "<b>Help</b>\n\n"
    chat_id = update.effective_chat.id
    msg = msg + "The futures trading simulator is absolutely free to use.\n"\
        "This bot shows the possibilities of working with futures - trading, calculating variation margin.\n"\
        "All futures are settled, the contract is based on cryptocurrency."
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML', reply_markup=reply_markup)


async def portfolio(update, context):
    tg_id = update.message.chat_id
    chat_id = update.effective_chat.id
    sql = sqlite3.connect('endless.db')
    db = sql.cursor()
    msg = "<b>Portfolio</b>\n\n"
    msg = msg + "CASH\n"
    result = db.execute('SELECT amount, currency FROM balances WHERE user_id =' + str(tg_id))
    rows = result.fetchall()
    for balance in rows:
        msg = msg + "<b>Virtual " + balance[1] + "</b>: " + str(balance[0]) + " " + balance[1] + "\n"
    msg = msg + "\nFUTURES\n"
    query = "select future.name, asset.count, ifnull(future.last_price, 0) last_price, future.count * pr.price new_price, future.currency, maxpr.timestamp from assets as asset"\
        " left join futures as future on asset.future = future.id"\
        " left join (select crypto, max(timestamp) as timestamp from prices group by crypto) maxpr on future.crypto = maxpr.crypto"\
        " left join prices pr on future.crypto = pr.crypto and maxpr.timestamp = pr.timestamp"\
        " where asset.user_id = " + str(tg_id)
    result = db.execute(query)
    rows = result.fetchall()
    last_date = None
    for balance in rows:
        msg = msg + "<b>" + balance[0] + "</b>: " + str(balance[1]) + " contracts\n" 
        diff = (round(balance[3], 2) - round(balance[2], 2)) * balance[1]
        msg = msg +  "<i>Planning Variation margin (VM): " + format(diff, ".2f") + " " + balance[4] + "</i>\n"
        last_date = balance[5]
    msg = msg + "\nPrice timestamp " + last_date
    sql.close() 
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML', reply_markup=reply_markup)
       

async def futures(update, context):
    tg_id = update.message.chat_id
    chat_id = update.effective_chat.id
    sql = sqlite3.connect('endless.db')
    db = sql.cursor()
    msg = "<b>Futures</b>\n\n"
    query = "select fut.id, fut.name, fut.crypto, fut.count, fut.mc_rate, fut.currency, cr.name as crypto_name,pr.price, pr.currency as price_currency from futures as fut "\
                        " left join crypto cr on fut.crypto = cr.code"\
                        " left join (select crypto, max(timestamp) as timestamp from prices group by crypto) maxpr on fut.crypto = maxpr.crypto "\
                        " left join prices pr on fut.crypto = pr.crypto and maxpr.timestamp = pr.timestamp"
    result = db.execute(query)
    rows = result.fetchall()
    for list in rows:       
        id = list[0]
        name = list[1]
        cpypto = list[2]
        count = list[3]
        rate = list[4]
        price = list[7]
        currency = list[8]
        full_price = float(count) * price
        free_balance = (float(count) * price) * float(rate) / 100.0
        msg = msg + "<b>" + name + "</b> - contains " + format(count, ".2f") + " " + cpypto + "\n"
        msg = msg + "<i>Contract amount:</i> " + format(full_price, ".2f")  + " " + currency + "\n"
        msg = msg + "<i>Free balance for contract:</i> " + format(free_balance, ".2f") + " " + currency + "\n"
        msg = msg + "Buy or sell /market_" + str(id) + "\n\n"
    sql.close()   
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML', reply_markup=reply_markup)   


async def market(update, context):
    chat_id = update.effective_chat.id
    answer = re.findall(r"\/market_(.+)", update.message.text)
    if (len(answer) == 0):
        message = "Error!\nPossible commands:\n/market_X"
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML', reply_markup=reply_markup) 
        return   
    id = int(answer[0])
    tg_id = update.message.chat_id
    sql = sqlite3.connect('endless.db')
    # get future info
    query = "select fut.id, fut.name, fut.crypto, fut.count, fut.mc_rate, fut.currency, cr.name as crypto_name,pr.price, pr.currency as price_currency from futures as fut"\
                        " left join crypto cr on fut.crypto = cr.code"\
                        " left join (select crypto, max(timestamp) as timestamp from prices group by crypto) maxpr on fut.crypto = maxpr.crypto"\
                        " left join prices pr on fut.crypto = pr.crypto and maxpr.timestamp = pr.timestamp where fut.id = " + str(id)
    db = sql.cursor()   
    result = db.execute(query)
    rows = result.fetchall()
    list = rows[0]     
    fut_id = list[0]
    fut_name = list[1]
    fut_cpypto = list[2]
    fut_count = list[3]
    fut_rate = list[4]
    fut_price = list[7]
    fut_currency = list[8]
    full_price = float(fut_count) * fut_price
    free_balance = (float(fut_count) * fut_price) * float(fut_rate) / 100.0
    # set msg
    msg = "<b>" + fut_name + "</b>\n"
    msg = msg + "Contains " + format(fut_count, ".2f") + " " + fut_cpypto + "\n"
    msg = msg + "<i>Contract amount:</i> " + format(full_price, ".2f")  + " " + fut_currency + "\n"
    msg = msg + "<i>Free balance for contract:</i> " + format(free_balance, ".2f") + " " + fut_currency + "\n"
    # check balances
    query = "select bal.user_id, bal.amount, IFNULL(ast.count, 0) as count, IFNULL((fut.count * pr.price) * fut.mc_rate /100, 0) as amount_pos, ast.future, bal.currency from balances as bal"\
        " left join assets as ast on bal.user_id = ast.user_id "\
        " left join futures as fut on ast.future = fut.id"\
        " left join (select crypto, max(timestamp) as timestamp from prices group by crypto) maxpr  on fut.crypto = maxpr.crypto"\
        " left join prices pr on fut.crypto = pr.crypto and maxpr.timestamp = pr.timestamp"\
        " where bal.user_id = " + str(tg_id) 
    db = sql.cursor()   
    result = db.execute(query)
    rows = result.fetchall()
    # add info to msg
    btn_buy = True
    btn_sell = True
    btn_close = True
    if len(rows) == 0:
        msg = msg + "\n<b>You now free amount to buy</b>"
        btn_buy = False
    else:
        balance = 0
        bal_currency = ""
        amount_pos = 0
        count = 0
        for asset in rows:
            balance = asset[1]
            bal_currency = asset[5]
            amount_pos = amount_pos + asset[3] * asset[2]
            if asset[4] == id:
                count = count + asset[2]
        if balance - amount_pos < free_balance:
            btn_buy = False
            btn_sell = False
        if count == 0:
            btn_close = False
        msg = msg + "\n<b>Free balance amount:</b> " + format(balance - amount_pos, ".2f") + " " + bal_currency
        msg = msg + "\n<b>You have:</b> " + str(count) + " contracts"
    # set inline keyb
    keyboard = []
    buttons = []
    if btn_buy:
        buttons.append(InlineKeyboardButton("Buy", callback_data="buy_" + str(id)))
    if btn_sell:    
        buttons.append(InlineKeyboardButton("Sell", callback_data="sell_" + str(id)))
    if btn_close:    
        buttons.append(InlineKeyboardButton("Close position", callback_data="close_" + str(id)))
    keyboard.append(buttons)    
    reply_markup = InlineKeyboardMarkup(keyboard)  
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML', reply_markup=reply_markup)          
    sql.close()           


async def echo(update, context):
    await update.message.reply_text("Use /help for help")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


async def buttons_actions(update, context):  
    sql = sqlite3.connect('endless.db')
    db = sql.cursor()    
    tg_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    bot = context.bot
    query = update.callback_query
    query.answer()
    query_data = query.data
    future_id = -1
    msg = ""
    if(query_data.find("buy_") > -1):
        future_id = int(query_data.replace("buy_", ""))
        query_data = "buy"
    if(query_data.find("sell_") > -1):
        future_id = int(query_data.replace("sell_", ""))
        query_data = "sell" 
    if(query_data.find("close_") > -1):
        future_id = int(query_data.replace("close_", ""))
        query_data = "close"
    query_sql = "select future.name, asset.count, ifnull(future.last_price, 0) last_price, future.count * pr.price new_price, future.currency, maxpr.timestamp from assets as asset"\
        " left join futures as future on asset.future = future.id"\
        " left join (select crypto, max(timestamp) as timestamp from prices group by crypto) maxpr on future.crypto = maxpr.crypto"\
        " left join prices pr on future.crypto = pr.crypto and maxpr.timestamp = pr.timestamp"\
        " where asset.user_id = " + str(tg_id) + " and asset.future = " + str(future_id)
    result = db.execute(query_sql)
    rows = result.fetchall()
    if query_data == "buy":
        if len(rows) == 0:
            # no future - add new
            db.execute("INSERT INTO assets(user_id, future, count) VALUES(?, ?, ?)", (str(tg_id), future_id, 1))
            sql.commit() 
        else:
            row = rows[0]
            count = row[1] + 1
            db.execute("update assets set count = ? where user_id = ? and future = ?", (count, str(tg_id), future_id))
            sql.commit()
        msg = "You buy 1 future contract. See more in /portfolio"
    elif query_data == "sell" or query_data == "close":
        if len(rows) == 0:
            # it's strange - button can view if count more than zero
            msg = "Error!"
        else:
            row = rows[0]
            count = row[1]
            new_count = count - 1
            if query_data == "close":
                new_count = 0
            if new_count == 0:
                db.execute("delete from assets where user_id = ? and future = ?", (str(tg_id), future_id))
                sql.commit() 
                msg = "You position was closed" 
            else:
                db.execute("update assets set count = ? where user_id = ? and future = ?", (new_count, str(tg_id), future_id))
                sql.commit()    
                msg = "You sell 1 future contract. See more in /portfolio"
            # update balance with Variation margin
            count_diff = count - new_count
            diff = (round(row[3], 2) - round(row[2], 2)) * count_diff
            query_sql = "select id, amount, currency from balances where currency = 'USD' and user_id = " + str(tg_id)
            result = db.execute(query_sql)
            rows = result.fetchall()
            if len(rows) == 0:
                # no balance - report user
                x = 0
            else:
                row = rows[0]
                balance = row[1]
                balance_id = row[0]
                new_balance = round(balance + diff, 2)
                db.execute("update balances set amount = ? where id = ?", (new_balance, balance_id))
                sql.commit()             
                msg = msg + "\nYour Variation margin is " + format(diff, ".2f") + " USD" + "\nNew balance is " + format(new_balance, ".2f") + " USD" 
    # update msg
    await query.edit_message_text(text=msg, parse_mode='HTML')                      
  

def main():

    application = ApplicationBuilder().token(bot_key).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("portfolio", portfolio))
    application.add_handler(CommandHandler("futures", futures))

    application.add_handler(CallbackQueryHandler(buttons_actions))

    set_handler = MessageHandler(filters.Regex(r"\/market_(.+)"), market)
    application.add_handler(set_handler)

    handler_1 = MessageHandler(filters.Regex(r"Portfolio"), portfolio)
    application.add_handler(handler_1) 
    handler_2 = MessageHandler(filters.Regex(r"Market"), futures)
    application.add_handler(handler_2) 

    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    application.add_handler(MessageHandler(filters.TEXT, echo))

    application.add_error_handler(error)

    application.run_polling()

if __name__ == '__main__':
    main()