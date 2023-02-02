# EndlessFutures

An example of a futures trading bot.

## SETUP

1. rename .env.example to .env
2. add CRYPTOCOMPARE_KEY from api.cryptocompare.com to .env
3. add BOT_KEY from https://t.me/BotFather
4. add to crontab run bot.py after reboot
5. add to crontab run load_prices.py every 1 minutes (or another interval)
6. add to crontab run calculate.py every 8 hours

## Futures & Crypto

Cryptocurrency is used as the underlying asset, but other assets can be used as well.

Cryptocurrency as specified in table _ _crypto _ _
+ name = userfriendly name
+ code = ticker for load prices from api.cryptocompare.com

Futures are specified in table _ _futures _ _
+ name = futures name
+ crypto = ticker from table _ _crypto _ _ 
+ count = how much crypto in one futures contract
+ mc_rate = blocked amount from balance for use futures contract
+ currency = USD
+ last_price = futures contract price when last time variation margin calculate

## Basic info about futures

Detail info how futures works [how futures works](https://www.investopedia.com/terms/f/futures.asp)

## Live Example

Detail info how futures works [Endless Futures Bot](https://t.me/EndlessFutures_bot)
