"""
属性查找优先级验证
优先级：数据描述符 > 实例 __dict__ > 非数据描述符/类属性 > __getattr__ > AttributeError
对应源码：Objects/object.c:1560  _PyObject_GenericGetAttrWithDict
"""


# ── 准备两种描述符 ──

class DataDesc:
    """数据描述符：同时有 __get__ 和 __set__"""
    def __get__(self, obj, owner):
        return f"DataDesc.__get__（obj={obj}）"
    def __set__(self, obj, value):
        print(f"  DataDesc.__set__ 被调用，value={value!r}")


class NonDataDesc:
    """非数据描述符：只有 __get__"""
    def __get__(self, obj, owner):
        return f"NonDataDesc.__get__（obj={obj}）"


# ── 优先级 1 vs 2 vs 3：数据描述符 > 实例 dict > 非数据描述符/类属性 ──

class Demo:
    data = DataDesc()        # 数据描述符
    nondata = NonDataDesc()  # 非数据描述符
    klass = "我是类属性"      # 普通类属性

    def __init__(self):
        # 故意往实例 dict 里塞三个同名 key
        self.__dict__['data'] = "实例dict里的data"
        self.__dict__['nondata'] = "实例dict里的nondata"
        self.__dict__['klass'] = "实例dict里的klass"


print("=" * 60)
print("优先级 1 > 2 > 3 验证")
print("=" * 60)

d = Demo()
print(f"\nd.data    = {d.data}")
print(f"d.nondata = {d.nondata}")
print(f"d.klass   = {d.klass}")
print(f"\n→ 数据描述符赢了实例dict；非数据描述符和类属性都输给了实例dict")


# ── 数据描述符的 __set__ 能拦截赋值 ──

print("\n" + "=" * 60)
print("数据描述符拦截赋值")
print("=" * 60)

print(f"\n赋值前 d.__dict__['data'] = {d.__dict__['data']!r}")
d.data = "新值"  # 会走 DataDesc.__set__，而不是写实例 dict
print(f"赋值后 d.__dict__['data'] = {d.__dict__['data']!r}")
print("→ __set__ 拦截了赋值，实例 dict 里的旧值没被覆盖（读 d.data 走的是 __get__）")


# ── property 是数据描述符 ──

class PropDemo:
    def __init__(self):
        self._x = 0
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        self._x = value

print("\n" + "=" * 60)
print("property 是数据描述符")
print("=" * 60)

p = PropDemo()
p.x = 42
print(f"\np.x       = {p.x}")
print(f"p.__dict__ = {p.__dict__}")
print(f"'x' 在 p.__dict__ 里吗: {'x' in p.__dict__}")
print("→ property 拦截了读写，'x' 不会出现在实例 dict 里，只有 '_x'")


# ── 优先级 4：__getattr__ 兜底 ──

class Fallback:
    real = "真实存在的属性"
    def __getattr__(self, name):
        return f"__getattr__ 兜底：{name} 不存在，但我给你造了一个"

print("\n" + "=" * 60)
print("优先级 4：__getattr__ 兜底")
print("=" * 60)

fb = Fallback()
print(f"\nfb.real   = {fb.real}")    # 正常查到，不走 __getattr__
print(f"fb.nope   = {fb.nope}")      # 前 3 步没找到 → __getattr__ 兜底


# ── 优先级 5：什么都没有就报错 ──

class NoFallback:
    pass

print("\n" + "=" * 60)
print("优先级 5：没定义 __getattr__ → AttributeError")
print("=" * 60)

nf = NoFallback()
try:
    nf.nope
except AttributeError as e:
    print(f"\nAttributeError: {e}")
