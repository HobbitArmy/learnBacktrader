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

    def log(self, txt, dt=None):
        """ Logging function for this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close value(收盘价)" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        if self.dataclose[0] < self.dataclose[-1]:
            if self.dataclose[-1] < self.dataclose[-2]:
                # price has been falling 3 sessions in a row … BUY
                self.log('BUY Create %.2f' % self.dataclose[0])
                self.buy()


if __name__ == '__main__':
    cerebro = bt.Cerebro()  # Create a cerebro entity
    cerebro.addstrategy(TestStrategy)   # Add a strategy

    datapath = './data/000938.SZ.csv'
    data = bt.feeds.GenericCSVData(
        dataname=datapath, datetime=0, open=1, close=4, high=2, low=3, volume=6,
        nullvalue=0.0, dtformat='%Y/%m/%d',
        fromdate=datetime.datetime(2021, 7, 14), todate=datetime.datetime(2022, 7, 13))
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    init_value = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run(preload=False)
    print('Final Profit Value: %.2f' % (cerebro.broker.getvalue()-init_value))
