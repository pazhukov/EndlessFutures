import sqlite3
import telegram
import os
from dotenv import load_dotenv

load_dotenv()

#load variables
bot_key = os.environ['BOT_KEY']

def main():
    diffs = {}
    vm = {}
    bot = telegram.Bot(token=bot_key)
    sql = sqlite3.connect('endless.db')
    db = sql.cursor() 
    # get new prices  
    query = "select cr.id, cr.crypto, cr.count, pr.price, ifnull(cr.last_price, 0) last_price, cr.count * pr.price new_price from futures as cr"\
                        " left join (select crypto, max(timestamp) as timestamp from prices group by crypto) maxpr on cr.crypto = maxpr.crypto"\
                        " left join prices pr on cr.crypto = pr.crypto and maxpr.timestamp = pr.timestamp"  
    result = db.execute(query)
    rows = result.fetchall()
    for row in rows:
        row_id = row[0]
        new_price = round(row[5],2)
        diffs[row_id] = new_price - row[4]
        db.execute("update futures set last_price = ? where id = ?", (new_price, row_id))
        sql.commit() 
    # Calc Variation margin
    query = "select asset.user_id, asset.future, asset.count from assets as asset"
    result = db.execute(query)
    rows = result.fetchall()
    for row in rows:
        user = row[0]
        future = row[1]
        count = row[2]
        current_diff = diffs[future]
        if vm.get(user) == None:
            vm[user] = 0
        vm[user] = vm[user] + current_diff * count
    # update balance
    for key, value in vm.items():
        query = "select id, amount, currency from balances where currency = 'USD' and user_id = " + key
        result = db.execute(query)
        rows = result.fetchall()
        if len(rows) == 0:
            # no balance
            x = 0
        else:
            row = rows[0]
            balance = row[1]
            balance_id = row[0]
            new_balance = round(balance + value, 2)
            db.execute("update balances set amount = ? where id = ?", (new_balance, balance_id))
            sql.commit()             
            msg = "Your Variation margin is " + format(value, ".2f") + " USD" + "\nNew balance is " + format(new_balance, ".2f") + " USD"
            bot.sendMessage(chat_id=int(key), text=msg)
    sql.close()


if __name__ == '__main__':
    main()    
