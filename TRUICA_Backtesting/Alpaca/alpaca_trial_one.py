import logging
import json

from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import REST
from ticker.BaseTicker import BaseTicker
from instruments.Instruments import Instruments
from models.TickData import TickData

class AlpacaTicker(BaseTicker):
  def __init__(self):
    super().__init__("alpaca")
    self.api = REST('PKNS1FFO8DLHOXFZ1ZLX', 'BCTQ6bGxXB6dnBgnCHRjKyn2XgVnUkA1l1JbKCoI', 'https://paper-api.alpaca.markets')

  def startTicker(self):
    if self.api == None:
      logging.error('AlpacaTicker startTicker: Cannot start ticker as api is empty')
      return
    
    self.stream = Stream(self.api.key_id, self.api.secret_key, self.api.base_url)
    self.stream.on_connect = self.on_connect
    self.stream.on_close = self.on_close
    self.stream.on_error = self.on_error
    self.stream.on_trade_update = self.on_trade_update
    self.stream.on_barset_update = self.on_barset_update
    self.stream.on_quote_update = self.on_quote_update

    logging.info('AlpacaTicker: Going to connect..')
    self.stream.connect()

  def stopTicker(self):
    logging.info('AlpacaTicker: stopping..')
    self.stream.stop_ws()

  def registerSymbols(self, symbols):
    logging.info('AlpacaTicker Subscribing symbols %s', symbols)
    self.stream.subscribe_bars(*symbols)

  def unregisterSymbols(self, symbols):
    logging.info('AlpacaTicker Unsubscribing symbols %s', symbols)
    self.stream.unsubscribe_bars(*symbols)

  def on_barset_update(self, msg):
    # convert alpaca specific bars to our system specific Ticks (models.TickData) and pass to super class function
    ticks = []
    for symbol, bar in msg.items():
      tick = TickData(symbol)
      tick.lastTradedPrice = bar.c
      tick.open = bar.o
      tick.high = bar.h
      tick.low = bar.l
      tick.close = bar.c
      tick.volume = bar.v
      ticks.append(tick)
      
    self.onNewTicks(ticks)

  def on_connect(self):
    self.onConnect()

  def on_close(self):
    self.onDisconnect()

  def on_error(self, exception):
    self.onError(exception)

  def on_trade_update(self, msg):
    self.onOrderUpdate(msg)

  def on_quote_update(self, msg):
    pass
