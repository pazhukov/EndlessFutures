import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv()

#load variables
api_key = os.environ['BYBIT_KEY']
api_secret = os.environ['BYBIT_SECRET']


def main():
    sql = sqlite3.connect('endless.db')
    session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)
    
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    db = sql.cursor()
    result = db.execute('SELECT code FROM crypto')
    rows = result.fetchall()
    for code in rows:
        crypto_code = code[0]
        symbol = crypto_code + "USDT"
        result = session.get_tickers(category="spot", symbol=symbol)
        if result["retMsg"] != "OK":
            continue
        
        usd = float(result["result"]["list"][0]["lastPrice"])
        db.execute("INSERT INTO prices(timestamp, crypto, price, currency) VALUES(?, ?, ?, ?)", (dt_string, code[0], usd, 'USD'))
        sql.commit()          
    sql.close()

if __name__ == '__main__':
    main()  