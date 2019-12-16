from __future__ import print_function

from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.tools import tushare
from pyalgotrade.technical import linreg

from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade import broker as basebroker


class LinearRegression(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, period):
        super(LinearRegression, self).__init__(feed, 100000)
        self.__instrument = instrument
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__lsr = linreg.LeastSquaresRegression(self.__prices, period)
        self.__slope = linreg.Slope(self.__prices, period)

    def getLastLR(self):
        return self.__lsr

    def onOrderUpdated(self, order):
        if order.isBuy():
            orderType = "Buy"
        else:
            orderType = "Sell"
        self.info("%s order %d updated - Status: %s" % (
            orderType, order.getId(), basebroker.Order.State.toString(order.getState())
        ))

    def onBars(self, bars):
        if self.__lsr[-1] is None or self.__slope[-1] is None:
            return

        r = 20 / 100
        k1 = 1 - r / 2
        k2 = 1 + r / 2

        shares = self.getBroker().getShares(self.__instrument)
        bar = bars[self.__instrument]
        if shares == 0 and (self.__prices[-1] < self.__lsr[-1] * k1):
            sharesToBuy = int(self.getBroker().getCash(False) * 0.9 / bar.getClose())
            self.info("Placing buy market order for %s shares, close %s" % (sharesToBuy, bar.getClose()))
            self.marketOrder(self.__instrument, sharesToBuy)
        elif shares > 0 and (self.__prices[-1] > self.__lsr[-1] * k2):
            self.info("Placing sell market order for %s shares, close %s" % (shares, bar.getClose()))
            self.marketOrder(self.__instrument, -1*shares)

def main(plot):
    instrument = "002415"

    # Download the bars.
    feed = tushare.build_feed("WIKI", [instrument], 2017, 2019, ".")

    strat = LinearRegression(feed, instrument, 120)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("linreg", strat.getLastLR())

    strat.run()
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
