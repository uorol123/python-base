# 1. __repr__(self) → 给开发者看的"无歧义"字符串

什么时候触发：
交互式 REPL 里直接敲对象名
print(obj) 如果没定义 __str__，会回退到 __repr__
repr(obj) 函数
日志、f"{obj!r}"

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return f"Point(x={self.x}, y={self.y})"

p = Point(1, 2)
print(p)            # Point(x=1, y=2)  ← 没有 __str__，自动用 __repr__
repr(p)             # 'Point(x=1, y=2)'
```

惯用法则：返回一个表达式，理想情况下 eval() 后能重建对象（Point(x=1, y=2) 比 <Point object> 好一万倍）。

# 2. __str__(self) → 给用户看的"好看"字符串

什么时候触发：str(obj)、print(obj)、f"{obj}"。

```python
class Money:
    def __init__(self, amount, currency="CNY"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        return f"Money({self.amount!r}, {self.currency!r})"   # 给开发者
    def __str__(self):
        return f"¥{self.amount:.2f}"                         # 给用户

m = Money(100)
print(m)               # ¥100.00
print(repr(m))         # Money(100, 'CNY')
```

心法：永远至少实现 __repr__；__str__ 看用户场景再说。

# 3. __format__(self, format_spec) → f-string / format() 完全自定义

什么时候触发：f"{obj:格式}"、format(obj, 格式)、"{}".format(obj, ...)。

```python
class Temperature:
    def __init__(self, celsius: float):
        self.c = celsius

    def __format__(self, spec: str) -> str:
        if spec == "C":
            return f"{self.c:.2f}°C"
        if spec == "F":
            return f"{self.c * 9/5 + 32:.2f}°F"
        if spec == "":
            return f"{self.c:.1f}°"
        raise ValueError(f"未知格式 {spec!r}")

t = Temperature(100)
print(f"{t:C}")       # 100.00°C
print(f"{t:F}")       # 212.00°F
print(f"{t}")         # 100.0°     ← format_spec 为空串
```

⚠️ 别让 __format__ 里死循环——一旦改成默认走 __str__，要小心 f"{self}" 触发自己。
