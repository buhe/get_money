import time
import json
from datetime import datetime
import akshare as ak
import os
import tkinter as tk
from tkinter import messagebox

class StockTrader:
    def __init__(self, initial_capital=7000):
        self.capital = initial_capital  # 初始资金
        self.holdings = 0  # 持股数量
        self.trade_history = []  # 交易历史
        self.buy_history = []  # 买入历史价格
        self.data_file = 'trade_history.json'
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
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
        confirm = messagebox.askyesno("确认买入", f"当前市场价: {price}\n确认要买入吗?")
        if not confirm:
            print("取消买入操作")
            return
        
        price_dialog = tk.Toplevel()
        price_dialog.title("输入成交价格")
        price_dialog.geometry("300x150")
        price_dialog.transient(self.root)  # 设置为root的临时窗口
        price_dialog.grab_set()  # 模态对话框
        
        price_var = tk.StringVar()
        tk.Label(price_dialog, text="请输入实际成交价格:").pack(pady=10)
        price_entry = tk.Entry(price_dialog, textvariable=price_var)
        price_entry.pack(pady=5)
        
        def submit():
            try:
                manual_price = float(price_var.get())
                if self.capital >= manual_price:
                    self.capital -= manual_price
                    self.holdings += 1
                    self.buy_history.append(manual_price)
                    trade = {
                        'type': 'buy',
                        'price': manual_price,
                        'quantity': 1,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'remaining_capital': self.capital
                    }
                    self.trade_history.append(trade)
                    self.save_history()
                    print(f"买入1股，价格：{manual_price}，剩余资金：{self.capital:.2f}")
                    messagebox.showinfo("交易成功", "买入成功！")
                    price_dialog.destroy()
                else:
                    messagebox.showerror("错误", "资金不足")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的价格")
        
        submit_btn = tk.Button(price_dialog, text="确认", command=submit)
        submit_btn.pack(pady=10)

    def sell(self, price):
        """执行卖出操作"""
        if self.holdings > 0:
            confirm = messagebox.askyesno("确认卖出", f"当前市场价: {price}\n确认要卖出吗?")
            if not confirm:
                print("取消卖出操作")
                return
            
            price_dialog = tk.Toplevel()
            price_dialog.title("输入成交价格")
            price_dialog.geometry("300x150")
            price_dialog.transient(self.root)  # 设置为root的临时窗口
            price_dialog.grab_set()  # 模态对话框
            
            price_var = tk.StringVar()
            tk.Label(price_dialog, text="请输入实际成交价格:").pack(pady=10)
            price_entry = tk.Entry(price_dialog, textvariable=price_var)
            price_entry.pack(pady=5)
            
            def submit():
                try:
                    manual_price = float(price_var.get())
                    self.capital += manual_price
                    self.holdings -= 1
                    trade = {
                        'type': 'sell',
                        'price': manual_price,
                        'quantity': 1,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'remaining_capital': self.capital
                    }
                    self.trade_history.append(trade)
                    if self.holdings == 0:
                        self.buy_history = []  # 清空买入历史
                    self.save_history()
                    print(f"卖出1股，价格：{manual_price}，剩余资金：{self.capital:.2f}")
                    messagebox.showinfo("交易成功", "卖出成功！")
                    price_dialog.destroy()
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的价格")
            
            submit_btn = tk.Button(price_dialog, text="确认", command=submit)
            submit_btn.pack(pady=10)

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