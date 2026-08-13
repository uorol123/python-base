"""
() 调用机制的对比演示
====================
核心结论：obj()  →  type(obj).__call__(obj)
() 这个操作符背后永远走 __call__，而且是「对象自己类型」的 __call__。

本文件对比三种对象的 () 行为：
  - 函数 func()
  - 类     Dog()
  - 实例   d()

运行：python3 call_mechanism_compare.py
"""

def divider(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ============================================================
# 1. 函数调用 func()
# ============================================================
divider("① 函数调用 func() —— 走 function.__call__")

def func():
    return "我是函数的返回值"

print(f"func        = {func}")
print(f"type(func)  = {type(func).__name__}")
print(f"type(func).__call__ = {type(func).__call__}")
print(f"callable(func) = {callable(func)}")
print(f"func() = {func()!r}")
print("→ func 是 function 类型，function.__call__ 负责『执行函数体』")


# ============================================================
# 2. 类调用 Dog() —— 走 type.__call__（就是源码 type_call，行1940）
# ============================================================
divider("② 类调用 Dog() —— 走 type.__call__ → __new__ + __init__")

class Dog:
    def __new__(cls):
        print("   [Dog.__new__] 分配内存")
        return super().__new__(cls)
    def __init__(self):
        print("   [Dog.__init__] 初始化")

print(f"Dog        = {Dog}")
print(f"type(Dog)  = {type(Dog).__name__}")          # type (Dog 的元类是 type)
print(f"type(Dog).__call__ = {type(Dog).__call__}")
print(f"callable(Dog) = {callable(Dog)}")
print("调用 Dog()：")
d = Dog()
print(f"→ Dog 是 type 类型，type.__call__ 负责『__new__+__init__ 造实例』")


# ============================================================
# 3. 验证 Dog() 就是 type.__call__(Dog)
# ============================================================
divider("③ 验证：Dog()  ==  type.__call__(Dog)")

d1 = Dog()                       # 正常写法
print(f"Dog()               → {d1}")
d2 = type.__call__(Dog)          # 直接调元类的 __call__
print(f"type.__call__(Dog)  → {d2}")
print("→ 两者完全等价：Dog() 本质就是 type.__call__(Dog)")


# ============================================================
# 4. 实例调用 d() —— 默认不行！
# ============================================================
divider("④ 实例调用 d() —— 默认不可调用")

class Cat:
    pass

c = Cat()
print(f"c          = {c}")
print(f"type(c)    = {type(c).__name__}")             # Cat
print(f"callable(c) = {callable(c)}")                 # False
print("试图调用 c()：")
try:
    c()
except TypeError as e:
    print(f"   TypeError: {e}")
print("→ 实例默认没有 __call__，不能当函数用")


# ============================================================
# 5. 让实例『像函数』—— 给类定义 __call__
# ============================================================
divider("⑤ 定义 __call__ 后，实例也能用 () 调用")

class Speaker:
    def __call__(self, text):
        return f"说：{text}"

s = Speaker()
print(f"type(s).__call__ = {type(s).__call__}")       # 现在 Dog(type=s) 有 __call__ 了
print(f"callable(s) = {callable(s)}")                 # True
print(f"s('你好') = {s('你好')!r}")
print("→ s() 走 Cat.__call__(s) = Speaker.__call__(s)")


# ============================================================
# 6. 总表
# ============================================================
divider("⑥ 三种对象的 () 行为总表")

rows = [
    ("func",      "function", "function.__call__", "执行函数体",            "True"),
    ("Dog (类)",  "type",     "type.__call__",     "__new__+__init__ 造实例","True"),
    ("c (实例)",  "Cat",      "Cat.__call__",      "默认没有 → 报错",       "False"),
    ("s (实例)",  "Speaker",  "Speaker.__call__",  "执行自定义 __call__",   "True"),
]
print(f"{'对象':<10} {'类型':<10} {'() 调谁的 __call__':<22} {'() 干什么':<26} {'callable'}")
print("-" * 80)
for r in rows:
    print(f"{r[0]:<10} {r[1]:<10} {r[2]:<22} {r[3]:<26} {r[4]}")

print("""
一句话总结：
  ()  →  type(obj).__call__(obj)
  - 函数走 function.__call__ → 执行函数体
  - 类走 type.__call__ (源码 type_call, typeobject.c:1940) → __new__+__init__ 造实例
  - 实例默认走 type(实例).__call__，但类没定义 __call__ 就不可调用
  - 『调用类 = 造实例』是 type.__call__ 写死了的行为，不是巧合
""")
