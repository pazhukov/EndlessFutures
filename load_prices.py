import requests
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

URL = "https://min-api.cryptocompare.com/data/price?fsym=#CRYPTO#&tsyms=USD&api_key=#APIKEY#"


load_dotenv()


#load variables
api_key = os.environ['CRYPTOCOMPARE_KEY']


def main():
    sql = sqlite3.connect('endless.db')
    
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    db = sql.cursor()
    result = db.execute('SELECT code FROM crypto')
    rows = result.fetchall()
    for code in rows:
        get_price = URL
        get_price = get_price.replace("#CRYPTO#", code[0])
        get_price = get_price.replace("#APIKEY#", api_key)
        price_http = requests.get(get_price)
        if price_http.status_code == 200:
            data_price = price_http.json()
            usd = float(data_price['USD'])
            db.execute("INSERT INTO prices(timestamp, crypto, price, currency) VALUES(?, ?, ?, ?)", (dt_string, code[0], usd, 'USD'))
            sql.commit()          
    sql.close()

if __name__ == '__main__':
    main()    
