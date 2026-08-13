"""
数据描述符完整示例
每个章节对应 readme.md 里的同名章节，可逐段运行观察输出
"""


# ══════════════════════════════════════════════════════════════
# 一、数据 vs 非数据：有没有 __set__ 的区别
# ══════════════════════════════════════════════════════════════

class WithSet:
    """数据描述符：有 __get__ + __set__"""
    def __get__(self, obj, owner):
        return "数据描述符的 __get__"
    def __set__(self, obj, value):
        print(f"  → 数据描述符的 __set__ 拦截了赋值: {value!r}")

class WithoutSet:
    """非数据描述符：只有 __get__"""
    def __get__(self, obj, owner):
        return "非数据描述符的 __get__"

class Demo1:
    a = WithSet()       # 数据描述符
    b = WithoutSet()    # 非数据描述符

print("=" * 60)
print("一、数据 vs 非数据描述符")
print("=" * 60)

d1 = Demo1()
print(f"\n读 d1.a: {d1.a}")
print(f"读 d1.b: {d1.b}")

print("\n给 d1.a 赋值 'x'：")
d1.a = "x"                                          # → __set__ 拦截
print(f"  d1.__dict__ 有 'a' 吗: {'a' in d1.__dict__}")  # False（被拦截了）

print("\n给 d1.b 赋值 'y'：")
d1.b = "y"                                          # 直接写实例 dict
print(f"  d1.__dict__ 有 'b' 吗: {'b' in d1.__dict__}")  # True（没被拦截）
print(f"  再读 d1.b: {d1.b!r}")                          # 'y' —— 描述符被遮蔽了！


# ══════════════════════════════════════════════════════════════
# 二、类型验证器（数据描述符的标准用法）
# ══════════════════════════════════════════════════════════════

class Typed:
    """类型验证器：赋值时检查类型，每个实例独立存储"""
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __set_name__(self, owner, name):
        self.name = name                              # Python 自动告知属性名

    def __get__(self, obj, owner):
        if obj is None:
            return self                               # 类访问返回描述符自身
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} 需要 {self.expected_type.__name__}，"
                f"收到 {type(value).__name__}"
            )
        obj.__dict__[self.name] = value               # 存进实例 dict

class Person:
    name = Typed(str)
    age = Typed(int)

print("\n" + "=" * 60)
print("二、类型验证器")
print("=" * 60)

p1 = Person()
p2 = Person()
p1.name = "张三"
p1.age = 25
p2.name = "李四"
p2.age = 30

print(f"\np1.name={p1.name!r}, p1.age={p1.age}")
print(f"p2.name={p2.name!r}, p2.age={p2.age}")
print("→ 每个实例各自的值，互不影响")

print("\n尝试 p1.age = '二十六'：")
try:
    p1.age = "二十六"
except TypeError as e:
    print(f"  TypeError: {e}")

# 类访问返回描述符自身
print(f"\nPerson.name（类访问）: {Person.name}")
print(f"  是 Typed 实例: {isinstance(Person.name, Typed)}")


# ══════════════════════════════════════════════════════════════
# 三、只读属性
# ══════════════════════════════════════════════════════════════

class ReadOnly:
    """只读数据描述符：__set__ 直接报错"""
    def __init__(self, value):
        self._value = value

    def __get__(self, obj, owner):
        if obj is None:
            return self
        return self._value

    def __set__(self, obj, value):
        raise AttributeError("只读属性，不能修改")

class Config:
    version = ReadOnly("1.0.0")

print("\n" + "=" * 60)
print("三、只读属性")
print("=" * 60)

c = Config()
print(f"\nc.version = {c.version}")
print("尝试 c.version = '2.0'：")
try:
    c.version = "2.0"
except AttributeError as e:
    print(f"  AttributeError: {e}")


# ══════════════════════════════════════════════════════════════
# 四、手写 property：数据描述符的等价实现
# ══════════════════════════════════════════════════════════════

class MyProperty:
    """用数据描述符实现 property 的核心逻辑"""
    def __init__(self, fget=None, fset=None, fdel=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = fget.__doc__ if fget else None

    def __get__(self, obj, owner):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("不可读")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("不可写")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("不可删")
        self.fdel(obj)

    def setter(self, fset):
        """模仿 @prop.setter 装饰器"""
        return MyProperty(self.fget, fset, self.fdel)

    def deleter(self, fdel):
        """模仿 @prop.deleter 装饰器"""
        return MyProperty(self.fget, self.fset, fdel)

class Temp:
    """用 MyProperty 实现带验证的温度属性"""
    def __init__(self, celsius=0):
        self._celsius = celsius

    @MyProperty
    def celsius(self):
        """摄氏度"""
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("温度不能低于绝对零度")
        self._celsius = value

print("\n" + "=" * 60)
print("四、手写 property")
print("=" * 60)

t = Temp(25)
print(f"\nt.celsius = {t.celsius}")
t.celsius = 100
print(f"设为 100 后: t.celsius = {t.celsius}")
print("尝试 t.celsius = -300：")
try:
    t.celsius = -300
except ValueError as e:
    print(f"  ValueError: {e}")

# 对比内置 property
print(f"\nTemp.celsius 是数据描述符: {hasattr(Temp.celsius, '__set__')}")
print(f"内置 property 也是数据描述符: {hasattr(property, '__set__')}")


# ══════════════════════════════════════════════════════════════
# 五、描述符必须是类属性
# ══════════════════════════════════════════════════════════════

class Desc:
    def __get__(self, obj, owner):
        return "触发了 __get__"

print("\n" + "=" * 60)
print("五、描述符必须是类属性")
print("=" * 60)

d = Demo1()  # 复用之前的类
# 放进实例 dict —— 协议不触发
d.__dict__['x'] = Desc()
print(f"\n实例 dict 里的描述符: {d.x}")
print("  → 没调 __get__，返回的是描述符对象本身")

# 放进类 dict —— 协议触发
Demo1.z = Desc()
print(f"\n类 dict 里的描述符: {d.z}")
print("  → 调了 __get__，返回了 '触发了 __get__'")
