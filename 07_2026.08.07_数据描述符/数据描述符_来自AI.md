--- 2026.08.07更新

# 数据描述符

## 一、什么是描述符

描述符是实现了 `__get__`、`__set__`、`__delete__` 中**至少一个**的对象。它必须作为**类属性**存在才能触发协议——放在实例 `__dict__` 里什么都不会发生。

Python 根据实现了哪些方法，把描述符分成两种：

| 类型 | 实现的方法 | 在属性查找链中的位置 | 常见例子 |
|---|---|---|---|
| **数据描述符** | `__get__` + (`__set__` 或 `__delete__`) | 优先级 1（高于实例 dict） | `property`、`__slots__` |
| **非数据描述符** | 只有 `__get__` | 优先级 3（低于实例 dict） | 普通方法（`function`） |

> 回顾上一篇（`04_04`）的源码：CPython 用 `PyDescr_IsData`（`descrobject.c:1028`）判断是不是数据描述符——检查 `tp_descr_set != NULL`（即有没有 `__set__` 或 `__delete__`）。只有数据描述符能在 L1592 命中、插队到实例 dict 前面。

---

## 二、描述符协议的三个方法

```python
__get__(self, obj, owner=None)
__set__(self, obj, value)
__delete__(self, obj)
```

### `__get__(self, obj, owner)`

读取时调用。两个场景：

```python
# 实例访问：obj.attr
descriptor.__get__(instance, type(instance))   # obj=实例, owner=类

# 类访问：Cls.attr
descriptor.__get__(None, Cls)                   # obj=None, owner=类
```

约定：当 `obj is None`（类访问）时，返回描述符自身。这样 `Cls.attr` 拿到的是描述符对象，`instance.attr` 拿到的是 `__get__` 的返回值。

### `__set__(self, obj, value)`

```python
# 赋值：obj.attr = value
descriptor.__set__(instance, value)
```

注意：**只有数据描述符（有 `__set__`）才能拦截赋值**。非数据描述符不拦截，赋值直接写进实例 dict，从此遮蔽掉描述符。

### `__delete__(self, obj)`

```python
# 删除：del obj.attr
descriptor.__delete__(instance)
```

### `__set_name__`（可选，Python 3.6+）

```python
# 类创建时自动调用，告诉描述符自己叫什么名字
descriptor.__set_name__(owner_class, 'attr_name')
```

这个钩子让你不用手动传名字，Python 在创建类时会自动把属性名告诉描述符。非常实用。

---

## 三、数据 vs 非数据的本质区别

**同一个描述符，有没有 `__set__`，在赋值时完全不同：**

```python
class WithSet:      # 数据描述符
    def __get__(self, obj, owner): return "读"
    def __set__(self, obj, value): print(f"写被拦截: {value}")

class WithoutSet:   # 非数据描述符
    def __get__(self, obj, owner): return "读"

class Demo:
    a = WithSet()
    b = WithoutSet()

d = Demo()
d.a = 1     # → WithSet.__set__ 被调用，打印"写被拦截: 1"
d.b = 1     # → 直接写进 d.__dict__['b']，描述符从此被遮蔽
print(d.b)  # → 1（读实例 dict），不再是"读"（描述符的 __get__ 被绕过了）
```

这就是为什么**只有数据描述符能可靠地控制读写**——没有 `__set__`，一次赋值就能让描述符失效。

---

## 四、手写数据描述符

### 存储的关键问题

描述符对象本身存在**类**的 `__dict__` 里，全类只有一份。如果往 `self.xxx` 里存数据，**所有实例共享同一份数据**——这通常不是你想要的。

要存**每个实例各自独立**的值，标准做法是：在 `__get__`/`__set__` 里**读写实例自己的 `__dict__`**，用一个约定好的 key：

```python
class TypedField:
    def __set_name__(self, owner, name):      # Python 自动告知属性名
        self.storage_key = f'_typed_{name}'    # 用前缀避免和别的属性冲突

    def __get__(self, obj, owner):
        if obj is None:                        # 类访问，返回描述符自身
            return self
        return obj.__dict__.get(self.storage_key)  # 从实例 dict 读

    def __set__(self, obj, value):
        # 在这里可以做验证
        obj.__dict__[self.storage_key] = value     # 写进实例 dict
```

> 为什么直接写 `obj.__dict__[key] = value` 不会触发 `__set__` 递归？因为你是在**直接操作 dict 对象**，绕过了属性访问协议（`__setattr__`）。只有 `obj.attr = value` 这种**属性赋值**才会走 `type(obj).__setattr__` → 描述符的 `__set__`。

### 完整示例 1：类型验证器

```python
class Typed:
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, owner):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(f"{self.name} 需要 {self.expected_type.__name__}，"
                            f"收到 {type(value).__name__}")
        obj.__dict__[self.name] = value

class Person:
    name = Typed(str)
    age = Typed(int)

p = Person()
p.name = "张三"    # ✅
p.age = 25         # ✅
p.age = "二十五"   # ❌ TypeError: age 需要 int，收到 str
```

### 完整示例 2：只读属性

```python
class ReadOnly:
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

c = Config()
print(c.version)   # 1.0.0
c.version = "2.0"  # ❌ AttributeError: 只读属性，不能修改
```

---

## 五、property 本质上就是数据描述符

`property` 是 C 实现的，但等价于以下 Python 数据描述符：

```python
class MyProperty:
    def __init__(self, fget=None, fset=None, fdel=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

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

    def setter(self, fset):
        return MyProperty(self.fget, fset, self.fdel)

# 用法和内置 property 一模一样
class Temp:
    def __init__(self):
        self._celsius = 0

    @MyProperty
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("低于绝对零度")
        self._celsius = value
```

`property` 做的事就是：把 getter/setter 函数包装成一个数据描述符。`@property` 装饰器本质上是**把这个函数变成一个有 `__get__` 和 `__set__` 的数据描述符**，放到类的 `__dict__` 里。

---

## 六、验证：描述符必须是类属性

```python
class Desc:
    def __get__(self, obj, owner):
        return "触发了"

class Demo:
    pass

d = Demo()
# ❌ 放进实例 dict —— 协议不触发
d.__dict__['x'] = Desc()
print(d.x)        # <__main__.Desc object>，没调 __get__

# ✅ 放进类 dict —— 协议触发
Demo.y = Desc()
print(d.y)        # "触发了"，__get__ 被调用了
```

因为属性查找协议是在 `_PyType_LookupRef(tp, name)`（搜 **type** 的 MRO）时触发的。实例 dict 里的对象不会经过 `tp_descr_get` 检查。

---

## 七、小结

| 问题 | 答案 |
|---|---|
| 什么是数据描述符 | 有 `__get__` + (`__set__` 或 `__delete__`) 的对象，作为类属性存在 |
| 为什么优先级最高 | 源码 L1592：`PyDescr_IsData` 为 true 时直接返回，不走实例 dict |
| 怎么存每个实例各自的值 | 在 `__get__`/`__set__` 里读写 `obj.__dict__[key]`，不存 `self` 上 |
| `property` 是什么 | C 实现的数据描述符，把 getter/setter 包装成拦截读写的对象 |
| 为什么必须是类属性 | 协议只在 `_PyType_LookupRef`（搜 type MRO）时触发，实例 dict 不走这个路径 |

配套示例代码见同目录 `descriptor_demo.py`。
