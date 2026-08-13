from dataclasses import dataclass
# 自己写一个描述符类，通过描述符类实现需求
"""
预设一个实际情况：
有一个类是钱包，属性有余额，未来收入，提前支出，未来收入时间，当前时间，未来支出时间。（时间类和金额都用int，方便一点）
1.时间 >= 未来收入时间时 余额 = 余额 + 未来收入，未来收入清零。未来支出时间设为 1000
2.时间 >= 未来支出时间 余额 = 余额 - 提前支出，提前支出清零。未来支出时间设为 1000
3.未来支出固定 500，收入固定 800.不能设置
4.设置未来 要同时设置时间，而且时间必须大于当前时间否则就拒绝。

1和2的判断触发通过 设置 当前时间来实现，当当前时间>=1000 时，程序结束

"""
"""
情况分析，这些输入都得是int，然后set时：
余额，不需要校验
未来时间（两个），要大于当前时间，要小于等于1000
收入和支出，要不能为负数
当前时间设置了就要校验，然后更新余额，收入/支出以及时间

大致分三种情况。设置三个描述符类
"""

def is_right_val(value:int) -> bool:
    if not isinstance(value, int) or value < 0 or value >1000:
        return False
    return True

class MoneyDes:
    def __init__(self,value):
        self.value = value
    def __get__(self, obj, owner):
        if self.value:
            return self.value
        return None
    def __set__(self, obj, value):
            print("只读")


class TimeDes:
    def __init__(self):
        self.value = 0
    def __get__(self, obj, owner):
        if self.value:
            return self.value
        return None

    def __set__(self, obj, value):
        if is_right_val(value):
            self.value = value
        else:
            print("传错了")

class TimeNowDes:
    def __init__(self):
        self.value = 100
    def __get__(self, obj, owner):
        if self.value:
            return self.value
        return None
    # 当前时间,0代表不用计算，1代表支出，2代表收入
    def __set__(self, obj, value):
        self.value = value
        future_time_out = obj.future_time_out
        future_time_in = obj.future_time_in
        money = obj.money
        if value >= future_time_out:
            money = money - obj.money_out
            obj.money_out = 0 # 被只读拒绝
            obj.future_time_out = 1000
        if value >= future_time_in:
            money = money + obj.money_in
            obj.money_in = 0 # 被只读拒绝
            obj.future_time_in = 1000
        obj.money = money

@dataclass
class Account:
    # 初始5000元
    money = 5000
    money_in = MoneyDes(800)
    money_out = MoneyDes(500)
    future_time_in = TimeDes()
    future_time_out = TimeDes()
    time = TimeNowDes()

a = Account()

# 300收入，500支出，700支出，900收入
a.future_time_in = 300
a.future_time_out = 500

print('-------初始------')
print(a.money)
time = 100
while a.time<=1000:
    a.time = a.time + 100
    print(f"----------当前时间:{a.time}")
    print(a.money)
    if(a.time == 600):
        a.future_time_in = 900
        a.future_time_out = 700
