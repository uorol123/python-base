--- 2026.08.07更新

# Python 的一切操作都经由 type 分发

## 一、核心原则

之前学到 `A(x)` 会去 `type(A)` 上找 `__call__` 来执行。这不是 `__call__` 的特殊待遇，而是 Python 的通用原则——**对对象的一切操作，都先去对象的 type 上找对应的协议方法，由 type 决定怎么做**。实例本身只是数据载体，**行为由 type 定义**。

| 表达式 | 实际调用 | type 上的方法 |
|---|---|---|
| `a(x)` | `type(a).__call__(a, x)` | `__call__` |
| `a.xxx`（读） | `type(a).__getattribute__(a, 'xxx')` | `__getattribute__` |
| `a.xxx = v`（写） | `type(a).__setattr__(a, 'xxx', v)` | `__setattr__` |
| `del a.xxx` | `type(a).__delattr__(a, 'xxx')` | `__delattr__` |
| `a + b` | `type(a).__add__(a, b)` | `__add__` |
| `len(a)` | `type(a).__len__(a)` | `__len__` |
| `a[b]` | `type(a).__getitem__(a, b)` | `__getitem__` |

### 源码印证：`a.xxx` 的 C 入口

```c
// Objects/object.c:1177  PyObject_GetAttr —— 这就是 a.xxx 的 C 入口
PyObject *PyObject_GetAttr(PyObject *v, PyObject *name)
{
    PyTypeObject *tp = Py_TYPE(v);           // 第一步：拿 type
    ...
    result = (*tp->tp_getattro)(v, name);    // 第二步：调 type 的 tp_getattro 槽
}
```

第一步永远是 `Py_TYPE(v)`——取对象的 type。然后调用 type 上的 `tp_getattro` 函数指针。对于绝大多数类，这个指针指向 `PyObject_GenericGetAttr`（即 `object.__getattribute__`）。跟 `__call__` 走 `tp_call` 是**完全同一个模式**。

---

## 二、属性查找的五级优先级

`object.__getattribute__` 对应的 C 函数是 `_PyObject_GenericGetAttrWithDict`（`Objects/object.c:1560`）。它实现了一条严格的查找链：

```
优先级从高到低：
1. 数据描述符（data descriptor，在 type 的 MRO 里）   ← 能"插队"到实例 dict 前面
2. 实例 __dict__
3. 非数据描述符 / 普通类属性（在 type 的 MRO 里）       ← 日常说的"去 type 查"
4. __getattr__（如果定义了，作为兜底）
5. AttributeError
```

### 逐级对照源码

```c
// Objects/object.c:1560  _PyObject_GenericGetAttrWithDict

// ── 先在 type 的 MRO 里查找（这一步拿到引用，但不一定立刻用）──
descr = _PyType_LookupRef(tp, name);              // L1587：搜 type 的 MRO

f = NULL;
if (descr != NULL) {
    f = Py_TYPE(descr)->tp_descr_get;             // 看它有没有 __get__
    if (f != NULL && PyDescr_IsData(descr)) {     // L1592：如果是数据描述符
        res = f(descr, obj, ...);                 // → 直接调 __get__，返回
        goto done;                                // ← 优先级 1：到这里就结束了
    }
}

// ── 查实例 __dict__ ──
if (dict != NULL) {
    int rc = PyDict_GetItemRef(dict, name, &res); // L1629
    if (res != NULL)
        goto done;                                // ← 优先级 2：实例 dict 命中就返回
}

// ── 回到最开始在 type MRO 里找到的东西 ──
if (f != NULL) {                                  // L1644：非数据描述符（有 __get__）
    res = f(descr, obj, ...);                     // → 调 __get__
    goto done;                                    // ← 优先级 3a
}
if (descr != NULL) {                              // L1653：普通类属性（没有 __get__）
    res = descr;                                  // → 直接返回
    goto done;                                    // ← 优先级 3b
}

// ── 都没找到 ──
PyErr_Format(PyExc_AttributeError, ...);          // L1660：报错（优先级 5）
```

**关键理解**：`_PyType_LookupRef`（L1587）在最开始就搜了一遍 type MRO，但**只有数据描述符会立即返回**（优先级 1）。如果不是数据描述符，先让位给实例 dict（优先级 2），实例 dict 也没有时才回来用它（优先级 3）。

> **这就是为什么笔记里"先查实例 dict，再查类"在日常场景下是对的**——因为普通的类属性（和方法）不是数据描述符，它们会让位给实例 dict。只有数据描述符能"插队"到实例 dict 前面。

### 具体追踪：同名时为什么实例属性赢

用 `changable.py` 的例子：类属性 `name = 'tdd'`（字符串），实例属性 `self.name = 'me'`，同名。读 `me.name` 时逐行走一遍：

```c
// L1587：搜 type MRO → 找到了 descr = 'tdd'（一个 str 对象）
descr = _PyType_LookupRef(tp, name);

f = NULL;
if (descr != NULL) {
    f = Py_TYPE(descr)->tp_descr_get;           // str 没有 __get__ → f = NULL
    if (f != NULL && PyDescr_IsData(descr)) {   // f 是 NULL → 条件为 false
        goto done;                              // ← 没进去！'tdd' 被扣住但不返回
    }
}

// L1629：查实例 __dict__
PyDict_GetItemRef(dict, name, &res);            // 找到了 'me'
goto done;                                      // ← 实例属性赢，返回 'me'

// L1653：普通类属性 → 永远走不到，因为上一步已经 return 了
```

**胜负手在 L1592**：类型 MRO 确实先搜了，也确实找到了 `'tdd'`。但 `'tdd'` 是普通字符串——没有 `__get__`、没有 `__set__`，不是数据描述符——所以 L1592 不命中，**放行去查实例 dict**。实例 dict 里有 `'me'`，命中返回。

如果类属性换成一个 `property`（数据描述符），L1592 就会命中并直接返回，实例 dict 连被检查的机会都没有：

```python
# 普通类属性：实例 dict 赢
class A:
    name = '类属性'           # str，不是描述符
    def __init__(self):
        self.name = '实例属性'
print(A().name)               # '实例属性'  ← 实例赢了（L1592 没命中 → L1629 命中）

# 数据描述符：类属性赢，实例 dict 被无视
class B:
    @property
    def name(self):            # property 是数据描述符
        return 'property值'
    def __init__(self):
        self.__dict__['name'] = '实例属性'  # 手动塞进实例 dict
print(B().name)               # 'property值' ← 类赢了（L1592 命中 → L1629 根本没走到）
```

> **一句话**：实例属性能赢，不是因为"Python 先查实例"，而是因为类属性是普通值（不是数据描述符），源码在 L1592 放行了，才让实例 dict 有机会在 L1629 被查到。

### 第 4 步：`__getattr__` 兜底

前 3 步都没找到时不一定立刻报错。如果 type 上定义了 `__getattr__`，Python 会调用它做最后的尝试：

```c
// Objects/typeobject.c:9621  _Py_slot_tp_getattr_hook
res = _PyObject_GenericGetAttrWithDict(self, name, NULL, 1);  // 先走完前 3 步
if (res == NULL && !PyErr_Occurred()) {
    res = call_attribute(self, getattr, name);  // ← 第 4 步：调 __getattr__
}
```

`__getattr__` 和 `__getattribute__` 的区别：

| | 调用时机 | 日常用途 |
|---|---|---|
| `__getattribute__` | **每次**属性访问都调用（无条件） | 极少自定义（容易无限递归） |
| `__getattr__` | 只在**正常查找失败后**才调用 | 动态属性、代理模式 |

---

## 三、什么是描述符

描述符是实现了 `__get__`、`__set__`、`__delete__` 中**至少 `__get__`** 的类。根据实现了哪些，分两种：

| 类型 | 实现的方法 | 在查找链中的位置 | 常见例子 |
|---|---|---|---|
| **数据描述符** | `__get__` + (`__set__` 或 `__delete__`) | 优先级 1（高于实例 dict） | `property`、`__slots__` |
| **非数据描述符** | 只有 `__get__` | 优先级 3（低于实例 dict） | 普通方法（`function`） |

CPython 判断数据描述符的依据（`Objects/descrobject.c:1028`）：

```c
int PyDescr_IsData(PyObject *ob)
{
    return Py_TYPE(ob)->tp_descr_set != NULL;  // 有 __set__/__delete__ 就是 data
}
```

**这就是 `property` 能拦截实例赋值的原因**：`property` 同时实现了 `__get__` 和 `__set__`，是数据描述符，优先级高于实例 dict。所以即便你往实例 dict 里手动塞一个同名 key，读的时候 `property.__get__` 依然优先。

---

## 四、验证

配套代码见同目录 `priority_demo.py`，可自行运行。核心结论：

```python
class DataDesc:        # 数据描述符：有 __get__ + __set__
    def __get__(self, obj, owner): return "DataDesc"
    def __set__(self, obj, value): pass

class NonDataDesc:     # 非数据描述符：只有 __get__
    def __get__(self, obj, owner): return "NonDataDesc"

class Demo:
    data = DataDesc()       # 数据描述符
    nondata = NonDataDesc() # 非数据描述符
    klass = "类属性"

    def __init__(self):
        # 往实例 dict 里故意塞三个同名 key
        self.__dict__['data']    = "实例dict"
        self.__dict__['nondata'] = "实例dict"
        self.__dict__['klass']   = "实例dict"

d = Demo()
print(d.data)     # DataDesc        ← 数据描述符赢了（优先级 1 > 2）
print(d.nondata)  # 实例dict         ← 非数据描述符输了（优先级 2 > 3）
print(d.klass)    # 实例dict         ← 普通类属性也输了（优先级 2 > 3）
```

---

## 五、为什么这样设计

1. **共享**：方法和大面积使用的默认值放在类上存一份，所有实例通过 type 链共享。不这样每个实例都得自备一份方法，内存浪费巨大。
2. **可定制**：因为查找逻辑在 type 的 `__getattribute__` 上，type 可以通过定义 `__getattr__`、描述符、`__slots__` 来改变行为。实例本身不需要任何配合。
3. **继承**：MRO 查找让子类自动获得父类的属性，不必复制。
4. **数据描述符优先于实例 dict**：让 `property` 这类工具能可靠地拦截读写，保证封装性。如果实例 dict 优先，任何人都可以 `obj.__dict__['x'] = ...` 绕过 property。

---

## 附：和之前知识的串联

| 已学 | 本文新增 |
|---|---|
| `A(x)` → `type(A).__call__` → `type.__new__/__init__`（造类） | `a.xxx` → `type(a).__getattribute__`（读属性） |
| `a(x)` → `type(a).__call__` → `A.__new__/A.__init__`（造实例） | `a.xxx = v` → `type(a).__setattr__`（写属性） |
| 一切实例化走 type 的 `__call__` | **一切操作都走 type 的对应协议方法** |

核心就一句话：**type 定义行为，实例持有数据，一切操作经由 type 分发**。
