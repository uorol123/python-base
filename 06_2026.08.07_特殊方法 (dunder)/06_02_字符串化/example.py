"""
__repr__ / __str__ / __format__ 渐进式示例
从什么都不定义到三个全定义，观察每一步输出怎么变
对应源码：object.c:662 (repr)、object.c:710 (str)、abstract.c:840 (format)
"""


# ══════════════════════════════════════════════════════════════
# 第 0 层：什么都不定义 → object 的默认实现
# ══════════════════════════════════════════════════════════════

class Money0:
    def __init__(self, amount, currency="CNY"):
        self.amount = amount
        self.currency = currency

m0 = Money0(100)
print("=== 第 0 层：什么都不定义 ===")
print(f"  print(m0): {m0}")          # <Money0 object at 0x...>
print(f"  repr(m0): {repr(m0)}")     # 同上
print(f"  str(m0):  {str(m0)}")      # 同上（object.__str__ 回退到 __repr__）
# 全是 <Money0 object at 0x...>，没有任何有用信息


# ══════════════════════════════════════════════════════════════
# 第 1 层：只定义 __repr__ → print/str/repr 全走它
# ══════════════════════════════════════════════════════════════
# 这就是源码里 object_str 的逻辑：没有 __str__ → 直接调 __repr__

class Money1:
    def __init__(self, amount, currency="CNY"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        # 给开发者看：理想情况下能 eval 重建对象
        return f"Money1(amount={self.amount!r}, currency={self.currency!r})"

m1 = Money1(100)
print("\n=== 第 1 层：只定义 __repr__ ===")
print(f"  print(m1): {m1}")          # Money1(amount=100, currency='CNY')
print(f"  repr(m1): {repr(m1)}")     # 同上
print(f"  str(m1):  {str(m1)}")      # 同上 ← object.__str__ 转发给 __repr__


# ══════════════════════════════════════════════════════════════
# 第 2 层：定义 __repr__ + __str__ → 开发者和用户看到不同的东西
# ══════════════════════════════════════════════════════════════

class Money2:
    def __init__(self, amount, currency="CNY"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        # 给开发者：调试、日志
        return f"Money2(amount={self.amount!r}, currency={self.currency!r})"

    def __str__(self):
        # 给用户：展示
        symbol = {"CNY": "¥", "USD": "$", "EUR": "€"}.get(self.currency, "")
        return f"{symbol}{self.amount:.2f}"

m2 = Money2(100, "USD")
print("\n=== 第 2 层：__repr__ + __str__ ===")
print(f"  print(m2): {m2}")          # $100.00        ← __str__
print(f"  str(m2):  {str(m2)}")      # $100.00        ← __str__
print(f"  repr(m2): {repr(m2)}")     # Money2(...)    ← __repr__
print(f"  f'{{m2}}': {f'{m2}'}")     # $100.00        ← __str__（空格式走 __format__→__str__）


# ══════════════════════════════════════════════════════════════
# 第 3 层：三个全定义 → f-string 格式也能自定义
# ══════════════════════════════════════════════════════════════

class Money3:
    def __init__(self, amount, currency="CNY"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        return f"Money3(amount={self.amount!r}, currency={self.currency!r})"

    def __str__(self):
        symbol = {"CNY": "¥", "USD": "$", "EUR": "€"}.get(self.currency, "")
        return f"{symbol}{self.amount:.2f}"

    def __format__(self, spec):
        """
        spec 是冒号后面的格式说明符
        f"{m:raw}"    → spec = "raw"
        f"{m}"        → spec = ""
        f"{m:>10}"    → spec = ">10"（内置对齐，但这里会被我们拦截）
        """
        if spec == "raw":
            return str(self.amount)             # 纯数字
        if spec == "symbol":
            return str(self)                     # 走 __str__
        if spec == "word":
            return f"{self.amount}元"            # 中文
        if spec == "":
            return str(self)                     # 空格式 → 走 __str__
        raise ValueError(f"未知格式: {spec!r}")

m3 = Money3(888, "CNY")
print("\n=== 第 3 层：三个全定义 ===")
print(f"  print(m3):       {m3}")              # ¥888.00        ← __str__
print(f"  repr(m3):        {repr(m3)}")        # Money3(...)    ← __repr__
print(f"  f'{{m3}}':        {f'{m3}'}")        # ¥888.00        ← __format__ spec=""
print(f"  f'{{m3:raw}}':    {f'{m3:raw}'}")    # 888            ← __format__ spec="raw"
print(f"  f'{{m3:word}}':   {f'{m3:word}'}")   # 888元          ← __format__ spec="word"
print(f"  f'{{m3:symbol}}': {f'{m3:symbol}'}") # ¥888.00        ← __format__ spec="symbol"


# ══════════════════════════════════════════════════════════════
# 补充：列表里的元素用 __repr__，不用 __str__
# ══════════════════════════════════════════════════════════════
# 这是常见坑：print 一个列表，元素走的是 __repr__ 不是 __str__

print("\n=== 补充：列表里元素走 __repr__ ===")
m_list = [Money2(100, "CNY"), Money2(200, "USD")]
print(f"  {m_list}")
# 输出 [Money2(amount=100, currency='CNY'), Money2(amount=200, currency='USD')]
# 不是 [¥100.00, $200.00] —— 因为容器内部用 repr() 展示元素
