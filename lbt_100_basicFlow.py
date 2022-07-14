"""
-*- coding: utf-8 -*-
@Author  : luxy

- learn back-trader quantum trading code
https://pythondict.com/quant/backtrader-easy-quant-one/

- data:
https://ca.finance.yahoo.com/

@Time    : 2022/7/14 9:29
"""
import datetime
import backtrader as bt


# 3. Creating Strategy
class TestStrategy(bt.Strategy):
    """
    Inherit and construct the strategy
    """

    def log(self, txt, dt=None, doprint=False):
        """ Uniform the log info """
        if doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        # 初始化相关数据
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 五日移动平均线
        self.sma5 = bt.indicators.SimpleMovingAverage(self.datas[0], period=5)
        # 十日移动平均线
        self.sma10 = bt.indicators.SimpleMovingAverage(self.datas[0], period=10)

    def notify_order(self, order):
        """
        Order status processing

        Arguments:
            order {object} -- 订单状态
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 如订单已被处理，则不用做任何事情
            return

        # 检查订单是否完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            self.bar_executed = len(self)

        # 订单因为缺少资金之类的原因被拒绝执行
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # 订单状态处理完成，设为空
        self.order = None

    def notify_trade(self, trade):
        """
        Trade result

        Arguments:
            trade {object} -- trade status
        """
        if not trade.isclosed:
            return

        # 显示交易的毛利率和净利润
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm), doprint=True)

    def next(self):
        """ Next execution """

        # 记录收盘价
        self.log('Close, %.2f' % self.dataclose[0])

        # 是否正在下单，如果是的话不能提交第二次订单
        if self.order:
            return

        # 是否已经买入
        if not self.position:
            # 还没买，如果 MA5 > MA10 说明涨势，买入
            if self.sma5[0] > self.sma10[0]:
                self.order = self.buy()
        else:
            # 已经买了，如果 MA5 < MA10 ，说明跌势，卖出
            if self.sma5[0] < self.sma10[0]:
                self.order = self.sell()

    def stop(self):
        self.log(u'(bullish and bearish MACD crossovers, make no sense/) Ending Value %.2f' %
                 (self.broker.getvalue()), doprint=True)


if __name__ == '__main__':
    # 1. Money and commission
    cerebro = bt.Cerebro()
    # 构建策略
    strats = cerebro.addstrategy(TestStrategy)
    # 每次买100股
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # 加载数据到模型中
    # 2. Load data
    data = bt.feeds.GenericCSVData(
        dataname='data/000938.csv',     # !!! Ascending Time Order
        fromdate=datetime.datetime(2019, 6, 1),
        todate=datetime.datetime(2020, 7, 14),
        dtformat='%Y/%m/%d',
        datetime=0,
        open=6,
        high=4,
        low=5,
        close=3,
        volume=11,
    )
    cerebro.adddata(data)
    # 设定初始资金和佣金
    cerebro.broker.setcash(50000.0)
    cerebro.broker.setcommission(0.005)
    # 策略执行前的资金
    init_value = cerebro.broker.getvalue()
    print('Beginning Money: %.2f' % cerebro.broker.getvalue())
    # 策略执行
    cerebro.run()
    print('Profit: %.2f' % (cerebro.broker.getvalue()-init_value))

    # Plot the overall progress
    cerebro.plot()


