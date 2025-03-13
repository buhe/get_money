import time
import json
from datetime import datetime
import akshare as ak
from playsound import playsound
import os

class StockTrader:
    def __init__(self, initial_capital=7000):
        self.capital = initial_capital  # 初始资金
        self.holdings = 0  # 持股数量
        self.trade_history = []  # 交易历史
        self.buy_history = []  # 买入历史价格
        self.data_file = 'trade_history.json'
        self.sound_dir = os.path.join(os.path.dirname(__file__), 'sounds')
        self.buy_sound = os.path.join(self.sound_dir, 'buy.wav')
        self.sell_sound = os.path.join(self.sound_dir, 'sell.wav')
        self.load_history()

    def load_history(self):
        """从文件加载交易历史"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.trade_history = data.get('trade_history', [])
                self.buy_history = data.get('buy_history', [])
                self.capital = data.get('capital', 7000)
                self.holdings = data.get('holdings', 0)
        except FileNotFoundError:
            pass

    def save_history(self):
        """保存交易历史到文件"""
        data = {
            'trade_history': self.trade_history,
            'buy_history': self.buy_history,
            'capital': self.capital,
            'holdings': self.holdings
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_current_price(self):
        """获取腾讯股票实时价格"""
        try:
            # 使用akshare获取腾讯股票（00700.HK）的实时价格
            stock_data = ak.stock_hk_spot_em()
            tencent_data = stock_data[stock_data['代码'] == '00700']
            if not tencent_data.empty:
                return float(tencent_data['最新价'].values[0])
            return None
        except Exception as e:
            print(f"获取股票价格时出错: {e}")
            return None

    def calculate_average_buy_price(self):
        """计算历史购买价格的均值"""
        if not self.buy_history:
            return None
        return sum(self.buy_history) / len(self.buy_history)

    def should_buy(self, current_price):
        """判断是否应该买入"""
        if not self.buy_history:  # 如果没有购买历史，直接买入
            return True
        avg_price = self.calculate_average_buy_price()
        return current_price < avg_price * 0.998  # 低于均值0.2%

    def should_sell(self, current_price):
        """判断是否应该卖出"""
        if not self.buy_history or self.holdings == 0:
            return False
        avg_price = self.calculate_average_buy_price()
        return current_price > avg_price * 1.003  # 高于均值0.3%

    def buy(self, price):
        """执行买入操作"""
        if self.capital >= price:
            self.capital -= price
            self.holdings += 1
            self.buy_history.append(price)
            trade = {
                'type': 'buy',
                'price': price,
                'quantity': 1,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'remaining_capital': self.capital
            }
            self.trade_history.append(trade)
            self.save_history()
            print(f"买入1股，价格：{price}，剩余资金：{self.capital:.2f}")
            playsound(self.buy_sound)

    def sell(self, price):
        """执行卖出操作"""
        if self.holdings > 0:
            self.capital += price
            self.holdings -= 1
            trade = {
                'type': 'sell',
                'price': price,
                'quantity': 1,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'remaining_capital': self.capital
            }
            self.trade_history.append(trade)
            if self.holdings == 0:
                self.buy_history = []  # 清空买入历史
            self.save_history()
            print(f"卖出1股，价格：{price}，剩余资金：{self.capital:.2f}")
            playsound(self.sell_sound)

    def run(self):
        """运行交易程序"""
        print("开始运行股票交易程序...")
        print(f"初始资金：{self.capital}，初始持股：{self.holdings}")

        while True:
            try:
                current_price = self.get_current_price()
                if current_price is None:
                    print("无法获取当前价格，等待下次尝试...")
                    time.sleep(10)  # 等待5分钟
                    continue

                print(f"\n当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"当前价格：{current_price}")
                print(f"当前资金：{self.capital:.2f}")
                print(f"当前持股：{self.holdings}")

                if self.should_buy(current_price):
                    self.buy(current_price)
                elif self.should_sell(current_price):
                    self.sell(current_price)
                else:
                    avg_price = self.calculate_average_buy_price()
                    if avg_price:
                        print(f"当前均价：{avg_price:.2f}，不满足交易条件")
                    else:
                        print("等待合适的交易机会...")

                time.sleep(10)  # 等待10秒

            except KeyboardInterrupt:
                print("\n程序已停止")
                break
            except Exception as e:
                print(f"发生错误：{e}")
                time.sleep(10)  # 发生错误时等待10秒

if __name__ == '__main__':
    trader = StockTrader()
    trader.run()