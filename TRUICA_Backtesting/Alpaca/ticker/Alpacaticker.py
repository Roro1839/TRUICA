import logging
from alpaca_trade_api.rest import REST, TimeFrame

from ordermgmt.Order import Order
from ordermgmt.BaseOrderManager import BaseOrderManager
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
        logging.info(f'{self.broker}: Going to place order with params {orderInputParams}')
        try:
            order = self.api.submit_order(
                symbol=orderInputParams.tradingSymbol,
                qty=orderInputParams.qty,
                side=orderInputParams.direction.value.lower(),
                type=orderInputParams.orderType.value.lower(),
                time_in_force="gtc",
                order_class=None,
                limit_price=orderInputParams.price,
                stop_price=orderInputParams.triggerPrice,
                client_order_id=f"{self.broker}-{orderInputParams.tradingSymbol}-{Utils.getEpoch()}")

            logging.info(f'{self.broker}: Order placed successfully, orderId = {order.id}')
            order = Order(orderInputParams)
            order.orderId = order.id
            order.orderPlaceTimestamp = Utils.getEpoch()
            order.lastOrderUpdateTimestamp = Utils.getEpoch()
            return order
        except Exception as e:
            logging.error(f'{self.broker} Order placement failed: {str(e)}')
            raise Exception(str(e))

    def modifyOrder(self, order, orderModifyParams):
        logging.info(f'{self.broker}: Going to modify order with params {orderModifyParams}')
        try:
            self.api.modify_position(
                symbol=order.tradingSymbol,
                qty=orderModifyParams.newQty if orderModifyParams.newQty > 0 else None,
                side=order.direction.value.lower(),
                type=order.orderType.value.lower(),
                limit_price=orderModifyParams.newPrice if orderModifyParams.newPrice > 0 else None,
                stop_price=orderModifyParams.newTriggerPrice if orderModifyParams.newTriggerPrice > 0 else None)

            logging.info(f'{self.broker}: Order modified successfully for orderId = {order.orderId}')
            order.lastOrderUpdateTimestamp = Utils.getEpoch()
            return order
        except Exception as e:
            logging.error(f'{self.broker} Order modify failed: {str(e)}')
            raise Exception(str(e))

    def modifyOrderToMarket(self, order):
        logging.info(f'{self.broker}: Going to modify order with params {order}')
        try:
            self.api.submit_order(
                symbol=order.tradingSymbol,
                qty=order.qty,
                side=order.direction.value.lower(),
                type='market',
                time_in_force="gtc",
                order_class=None,
                limit_price=None,
                stop_price=None,
                client_order_id=f"{self.broker}-{order.tradingSymbol}-{Utils.getEpoch()}")

            logging.info(f'{self.broker}: Order modified successfully to MARKET for orderId = {order.orderId}')
            order.lastOrderUpdateTimestamp = Utils.getEpoch()
            return order
        except Exception as e:
            logging.error(f'{self.broker} Order modify to market failed: {str(e)}')
            raise Exception(str(e))

    def cancelOrder(self, order):
        logging.info(f'{self.broker} Going to cancel order {order.orderId}')
        try:
            self.api.cancel_order(
                symbol=order.tradingSymbol,
                id=order.orderId)

            logging.info(f'{self.broker} Order cancelled successfully, orderId = {order.orderId}')
            order.lastOrderUpdateTimestamp = Utils.getEpoch()
            return order
        except Exception as e:
            logging.error(f'{self.broker} Order cancel failed: {str(e)}')
            raise Exception(str(e))

    def fetchAndUpdateAllOrderDetails(self, orders):
        logging.info(f'{self.broker} Going to fetch order book')
        try:
            account = self.api.get_account()
            positions = self.api.list_positions()

            for position in positions:
                foundOrder = next((o for o in orders if o.tradingSymbol == position.symbol), None)
                if foundOrder:
                    logging.info(f'Updated order for {foundOrder.tradingSymbol}')
                    foundOrder.qty = position.quantity
                    foundOrder.filledQty = position.market_value / position.avg_entry_price
                    foundOrder.pendingQty = 0
                    foundOrder.orderStatus = OrderStatus.ACTIVE
                    foundOrder.price = position.avg_entry_price
                    foundOrder.triggerPrice = 0
                    foundOrder.averagePrice = position.avg_entry_price
                    logging.info(f'{self.broker} Updated order {foundOrder}')

        except Exception as e:
            logging.error(f'{self.broker} Failed to fetch order details: {str(e)}')

    def convertToBrokerProductType(self, productType):
        if productType == ProductType.MIS:
            return "MIS"
        elif productType == ProductType.NRML:
            return "NRML"
        elif productType == ProductType.CNC:
            return "CNC"
        return None

    def convertToBrokerOrderType(self, orderType):
        if orderType == OrderType.LIMIT:
            return "limit"
        elif orderType == OrderType.MARKET:
            return "market"
        elif orderType == OrderType.SL_MARKET:
            return "stop_market"
        elif orderType == OrderType.SL_LIMIT:
            return "stop_limit"
        return None

    def convertToBrokerDirection(self, direction):
        if direction == Direction.LONG:
            return "buy"
        elif direction == Direction.SHORT:
            return "sell"
        return None
