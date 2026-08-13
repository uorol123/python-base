"""
def 与 function 的实验
======================
核心结论：
  1. def 是「编译函数体成 code 对象 + 造一个 function 实例」的语法糖。
  2. def 语句里的 () 是【形参列表】，不是调用运算符 → 不触发 __call__。
  3. 只有写 表达式()（如 f()）时，() 才是调用 → type(f).__call__(f)。
  4. function 类型的元类是 type，父类是 object，自己实现了 __call__。

运行：python3 def_and_function.py
"""

import dis
import types


def divider(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ============================================================
# 1. def 创建的是一个 function 类型的『对象』
# ============================================================
divider("① def 创建的是 function 类型的对象")

def greet(name):
    return f"hello, {name}"

print(f"greet       = {greet}")
print(f"type(greet) = {type(greet).__name__}")        # function
print(f"greet 是 function 类型的实例？ {isinstance(greet, types.FunctionType)}")
print("→ def 没有调用 greet，只是『造』出了它（一个对象）")


# ============================================================
# 2. 字节码铁证：def 里没有 CALL，()是参数列表
# ============================================================
divider("② 字节码：def 的 () 不是调用（无 CALL 指令）")

print("代码: def f(a, b): return a + b\n")
dis.dis(compile("def f(a, b): return a + b", "<str>", "exec"))
print("→ 只有 MAKE_FUNCTION + STORE_NAME，【没有 CALL】！")
print("→ () 里的 a, b 是形参，编译后进了 code 对象，不产生调用")

print()
print("对比：真正的调用 f(1, 2) 才有 CALL\n")
dis.dis(compile("f(1, 2)", "<str>", "exec"))
print("→ 这里有 CALL，这个 () 才是调用运算符")


# ============================================================
# 3. 定义 vs 调用：定义时函数体不执行
# ============================================================
divider("③ 定义时不执行，调用时才执行")

def shout():
    print("   [shout 函数体] 我被调用了！")

print("【阶段A】def shout() 写完 —— 函数体没跑")
print("【阶段B】现在调用 shout()：")
shout()
print("→ def 只是『注册』函数对象；shout() 才『执行』它")


# ============================================================
# 4. function 类型的结构：元类=type，父类=object，有 __call__
# ============================================================
divider("④ function 类型的结构")

print(f"function 类型本身        = {types.FunctionType}")
print(f"type(function 类型)      = {type(types.FunctionType).__name__}")   # type
print(f"function 的父类          = {types.FunctionType.__bases__}")        # (object,)
print(f"function 有 __call__？   {hasattr(types.FunctionType, '__call__')}")
print()
print("所以函数能被调用，是因为『function 类型实现了 __call__』")
print("而 object 没有 __call__ → 普通实例默认不可调用")


# ============================================================
# 5. f() 的执行路径：() → type(f).__call__(f)
# ============================================================
divider("⑤ f() 的执行路径")

def add(a, b):
    return a + b

print("f() 的完整路径：")
print("  add(1, 2)")
print("    → type(add).__call__(add, 1, 2)     # () 在 add 的类型上找 __call__")
print("    → function.__call__(add, 1, 2)       # function 类型有 __call__")
print("    → 执行 add 的函数体，返回结果")
print(f"  结果 = {add(1, 2)}")


# ============================================================
# 6. def 是语法糖：手工造一个等价的函数
# ============================================================
divider("⑥ def 是语法糖 —— 手工造函数")

# def 出来的函数，内部有 __code__（编译好的字节码）
def square(x):
    return x * x

print(f"def 出来的 square: {square}")
print(f"square.__code__ = {square.__code__}")    # 函数体的 code 对象
print(f"square(5) = {square(5)}")

# 手工用 types.FunctionType 造一个等价的
manual_square = types.FunctionType(
    square.__code__,     # 复用同样的字节码
    globals(),           # 全局命名空间
    "manual_square"      # 函数名
)
print(f"\n手工造的 manual_square: {manual_square}")
print(f"manual_square(5) = {manual_square(5)}")
print("→ 两者本质一样：def 就是『编译函数体成 code + 造 function 实例』")


# ============================================================
# 7. () 符号的重载：位置决定含义
# ============================================================
divider("⑦ () 符号是重载的 —— 位置决定含义")

rows = [
    ("f(a, b)",     "def 语句里",   "形参列表",        "MAKE_FUNCTION（无 CALL）"),
    ("f(1, 2)",     "表达式里",     "调用运算符",      "CALL → __call__"),
    ("class D(B):", "class 语句里", "基类列表",        "（class 机制另调元类）"),
    ("(a + b) * c", "表达式里",     "分组括号",        "改运算优先级"),
    ("(1, 2, 3)",   "表达式里",     "元组字面量",      "造 tuple"),
]
print(f"{'代码':<14}{'出现位置':<14}{'() 的身份':<16}{'字节码/效果'}")
print("-" * 70)
for r in rows:
    print(f"{r[0]:<14}{r[1]:<14}{r[2]:<16}{r[3]}")
print()
print("关键：def 里的 () 和 表达式里的 () 长得一样，但身份完全不同")
print("→ def 的 () 不触发 __call__，不是被 def『挡住』了，是它从来就不是调用")


# ============================================================
# 8. 总表
# ============================================================
divider("⑧ 总表")

print("""
┌─────────────┬──────────────────────────────────────────────┐
│ def xx():   │ 语法糖：编译函数体成 code + 造 function 实例   │
│             │   - () 是形参列表，不是调用                    │
│             │   - 字节码 MAKE_FUNCTION，没有 CALL            │
│             │   - 定义时函数体不执行                         │
├─────────────┼──────────────────────────────────────────────┤
│ xx()        │ 调用运算符                                    │
│             │   - () 在表达式里 = 调用                       │
│             │   - 字节码有 CALL                              │
│             │   - type(xx).__call__(xx) → 执行函数体         │
├─────────────┼──────────────────────────────────────────────┤
│ function    │ 函数对象的类型                                 │
│             │   - 元类 = type，父类 = object                 │
│             │   - 自己实现了 __call__（执行函数体）           │
│             │   - 这就是函数能被 () 调用的原因                │
└─────────────┴──────────────────────────────────────────────┘

一句话：
  def 是『造函数』，() 是『调函数』——
  def 里的 () 是参数容器，表达式里的 () 才是调用（→ __call__）。
  造出来的 function 实例之所以能被调用，是因为 function 类型实现了 __call__。
""")
