"""
-*- coding: utf-8 -*-
@Author  : luxy

- Backtrader-Doc: Quickstart Guide
https://www.backtrader.com/docu/quickstart/quickstart/

@Time    : 2022/7/14 13:31
"""

import backtrader as bt
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('printlog', False),
    )

    def log(self, txt, dt=None, doprint=False):
        """ Logging function for this strategy"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close value(收盘价)" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.maperiod)

        # % Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25,
        #                                     subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' %
                         (order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice, self.buycomm= order.executed.price, order.executed.comm
            elif order.issell():
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' %
                         (order.executed.price, order.executed.value, order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            # if self.dataclose[0] < self.dataclose[-1]:
            #     if self.dataclose[-1] < self.dataclose[-2]:
            #         # price has been falling 3 sessions in a row … BUY
            if self.dataclose[0] > self.sma[0]:
                self.log('BUY Create %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
        else:
            # Already in the market ... we might sell
            # if len(self) >= (self.bar_executed + self.params.exitbars):
            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' %
                 (self.params.maperiod, self.broker.getvalue()), doprint=True)


if __name__ == '__main__':
    cerebro = bt.Cerebro()  # Create a cerebro entity

    # % Add a strategy
    # cerebro.addstrategy(TestStrategy)
    cerebro.optstrategy(TestStrategy, maperiod=range(10, 31))
    # To optimize from 10~30


    datapath = './data/000938.SZ.csv'
    data = bt.feeds.GenericCSVData(
        dataname=datapath, datetime=0, open=1, close=4, high=2, low=3, volume=6,
        nullvalue=0.0, dtformat='%Y/%m/%d',
        fromdate=datetime.datetime(2021, 1, 14), todate=datetime.datetime(2022, 7, 14))
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set starting conditions
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission rate per operation
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    init_value = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run(preload=False, maxcpus=1)
    # maxcpus: How many cores to use simultaneously for optimization
    print('Final Profit Value: %.2f' % (cerebro.broker.getvalue() - init_value))

    cerebro.plot()

