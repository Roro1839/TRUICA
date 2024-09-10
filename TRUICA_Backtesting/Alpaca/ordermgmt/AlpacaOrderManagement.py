import logging
from alpaca_trade_api.rest import REST, TimeFrame

from ordermgmt.BaseOrderManager import BaseOrderManager
from ordermgmt.Order import Order

from models.ProductType import ProductType
from models.OrderType import OrderType
from models.Direction import Direction
from models.OrderStatus import OrderStatus

from utils.Utils import Utils

class AlpacaOrderManager(BaseOrderManager):
  def __init__(self):
    super().__init__("alpaca")
    self.api = REST('PKNS1FFO8DLHOXFZ1ZLX', 'BCTQ6bGxXB6dnBgnCHRjKyn2XgVnUkA1l1JbKCoI', 'https://paper-api.alpaca.markets')

  def placeOrder(self, orderInputParams):
    logging.info('%s: Going to place order with params %s', self.broker, orderInputParams)
    try:
      order = self.api.submit_order(
        symbol=orderInputParams.tradingSymbol,
        qty=orderInputParams.qty,
        side=self.convertToBrokerDirection(orderInputParams.direction),
        type=self.convertToBrokerOrderType(orderInputParams.orderType),
        time_in_force="gtc",
        order_class=None,
        limit_price=orderInputParams.price,
        stop_price=orderInputParams.triggerPrice,
        client_order_id=f"{self.broker}-{orderInputParams.tradingSymbol}-{Utils.getEpoch()}")

      logging.info('%s: Order placed successfully, orderId = %s', self.broker, order.id)
      order = Order(orderInputParams)
      order.orderId = order.id
      order.orderPlaceTimestamp = Utils.getEpoch()
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.error('%s Order placement failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def modifyOrder(self, order, orderModifyParams):
    logging.info('%s: Going to modify order with params %s', self.broker, orderModifyParams)
    try:
      self.api.modify_position(
        symbol=order.tradingSymbol,
        qty=orderModifyParams.newQty if orderModifyParams.newQty > 0 else None,
        side=self.convertToBrokerDirection(order.direction),
        type=self.convertToBrokerOrderType(order.orderType),
        limit_price=orderModifyParams.newPrice if orderModifyParams.newPrice > 0 else None,
        stop_price=orderModifyParams.newTriggerPrice if orderModifyParams.newTriggerPrice > 0 else None)

      logging.info('%s Order modified successfully for orderId = %s', self.broker, order.orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.error('%s Order modify failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def modifyOrderToMarket(self, order):
    logging.info('%s: Going to modify order with params %s', self.broker)
    try:
      self.api.submit_order(
        symbol=order.tradingSymbol,
        qty=order.qty,
        side=self.convertToBrokerDirection(order.direction),
        type='market',
        time_in_force="gtc",
        order_class=None,
        limit_price=None,
        stop_price=None,
        client_order_id=f"{self.broker}-{order.tradingSymbol}-{Utils.getEpoch()}")

      logging.info('%s Order modified successfully to MARKET for orderId = %s', self.broker, order.orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.error('%s Order modify to market failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def cancelOrder(self, order):
    logging.info('%s Going to cancel order %s', self.broker, order.orderId)
    try:
      self.api.cancel_order(
        symbol=order.tradingSymbol,
        id=order.orderId)

      logging.info('%s Order cancelled successfully, orderId = %s', self.broker, order.orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.error('%s Order cancel failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def fetchAndUpdateAllOrderDetails(self, orders):
    logging.info('%s Going to fetch order book', self.broker)
    try:
      account = self.api.get_account()
      positions = self.api.list_positions()

      for position in positions:
        foundOrder = next((o for o in orders if o.tradingSymbol == position.symbol), None)
        if foundOrder:
          logging.info('Updated order for %s', foundOrder.tradingSymbol)
          foundOrder.qty = position