# `type` 与 `object` 的 `__new__` / `__init__` 源码笔记

> 基于 CPython 源码（`Objects/typeobject.c`）。所有行号都指向该文件，除非另注明。
> 配合实证代码（`python3 -c "..."`）一起看更直观。

---

## 0. 一张图先建立全局认知

```
        ┌──────────────────────────────────────────────────────┐
        │   object  (PyBaseObject_Type, 行7243)                │
        │   ── 所有类的最终祖先                                 │
        │   ── tp_new  = object_new   (~15行)  造普通实例        │
        │   ── tp_init = object_init  (~18行)  啥也不做          │
        │   ── tp_call = NULL (用默认)                          │
        └──────────────────────────────────────────────────────┘
                              ▲
                              │ 继承
        ┌──────────────────────────────────────────────────────┐
        │   type   (PyType_Type, 行5985)                       │
        │   ── object 的子类：type.__bases__ == (object,)      │
        │   ── 但【重写】了 __new__ / __init__ / __call__       │
        │   ── tp_new  = type_new     (~838行)  造"类对象"      │
        │   ── tp_init = type_init    (~19行)   只校验参数       │
        │   ── tp_call = type_call    (行1940)  含 type(x) 特例 │
        └──────────────────────────────────────────────────────┘
```

**核心结论**：`type` 确实继承自 `object`，但它**重写了** `__new__` 和 `__init__`。
因为「造一个普通实例」和「造一个完整的类」复杂度天差地别——`object_new` 那十几行根本扛不住造类的工作。

实证：

```python
>>> type.__bases__
(<class 'object'>,)
>>> issubclass(type, object)
True
>>> type.__new__  is object.__new__    # 不同的 C 函数
False
>>> type.__init__ is object.__init__
False
>>> '__new__' in type.__dict__         # type 自己定义的，不是继承来的
True
```

---

## 1. 它们「本质是函数吗」？—— 不是

一个常见误解：`__new__`/`__init__` 是函数。**不是 `function` 类型**。

```python
>>> import types
>>> object.__new__
<built-in method __new__ of type object at 0xa43820>
>>> type(object.__new__).__name__
'builtin_function_or_method'
>>> isinstance(object.__new__, types.FunctionType)
False
>>> hasattr(object.__new__, '__code__')   # 没有字节码
False

>>> object.__init__
<slot wrapper '__init__' of 'object' objects>
>>> type(object.__init__).__name__
'wrapper_descriptor'
```

| 类型 | Python 里叫什么 | 本质 |
|------|----------------|------|
| `function` | 函数 | `def`/`lambda` 创建，带 `__code__`/`__globals__` |
| `builtin_function_or_method` | 内置方法 | 包着 **C 函数指针** |
| `wrapper_descriptor` | 槽位包装器 | 包着 **类型槽位里的 C 函数指针** |

准确说法：`object.__new__` / `object.__init__` 是**包着 C 函数指针的「可调用描述符」**，不是函数。这也解释了为什么 `inspect.getsource()` 取不到它们的源码——它们没有 Python 字节码，只有 C 实现。

---

## 2. C 槽位机制：C 函数怎么变成 Python 属性

`object` 和 `type` 在 C 里都是一张巨大的结构体表，每个字段叫一个**「槽位 (slot)」**。访问 `xxx.__new__` 时，类型系统从 `tp_new` 槽位里把那个 C 函数指针包成一个描述符交给你。

### `object` 的 C 定义 —— `PyBaseObject_Type`（行 7243）

```c
PyTypeObject PyBaseObject_Type = {
    "object",                       /* tp_name */
    sizeof(PyObject),               /* tp_basicsize */
    object_dealloc,                 /* tp_dealloc  ← 析构 */
    object_repr,                    /* tp_repr     ← repr() */
    ...
    object_init,                    /* tp_init  ← C 函数 object_init 塞进这个槽 */
    PyType_GenericAlloc,            /* tp_alloc ← 通用内存分配器 */
    object_new,                     /* tp_new   ← C 函数 object_new 塞进这个槽 */
    PyObject_Del,                   /* tp_free */
    ...
};
```

### `type` 的 C 定义 —— `PyType_Type`（行 5985）

```c
PyTypeObject PyType_Type = {
    "type",
    sizeof(PyHeapTypeObject),
    type_dealloc,
    ...
    type_call,                      /* tp_call  ← type(x)/type(name,bases,dict) 都走这(行1940) */
    ...
    type_init,                      /* tp_init  ← type 自己的，不是 object_init(行3383) */
    0,                              /* tp_alloc */
    type_new,                       /* tp_new   ← type 自己的，不是 object_new(行4261) */
    PyObject_GC_Del,                /* tp_free */
    ...
};
```

> 注意 `type` 这张表里 `tp_init`/`tp_new`/`tp_call` 全是 `type_*` 版本——这就是「重写」在 C 层的样子。

---

## 3. `object.__init__` 源码 —— 啥也不干（行 6087）

```c
static int
object_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyTypeObject *type = Py_TYPE(self);
    if (excess_args(args, kwds)) {              // 如果传了多余参数
        if (type->tp_init != object_init) {
            PyErr_SetString(PyExc_TypeError,
                "object.__init__() takes exactly one argument (the instance to initialize)");
            return -1;
        }
        if (type->tp_new == object_new) {
            PyErr_Format(PyExc_TypeError,
                "%.200s.__init__() takes exactly one argument (the instance to initialize)",
                type->tp_name);
            return -1;
        }
    }
    return 0;   // ← 否则直接返回，什么都不做！
}
```

**伪代码概括**：`检查别乱传参数 → return 0`。基类 `__init__` 就是个占位，真正的初始化由你的子类完成。

```python
>>> object(123)
TypeError: object() takes no arguments   # ← 就是这里报的
```

---

## 4. `object.__new__` 源码 —— 分配一块内存（行 6107）

```c
static PyObject *
object_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    if (excess_args(args, kwds)) {              // ① 拒绝乱传参数
        if (type->tp_new != object_new) {
            PyErr_SetString(PyExc_TypeError,
                "object.__new__() takes exactly one argument (the type to instantiate)");
            return NULL;
        }
        if (type->tp_init == object_init) {
            PyErr_Format(PyExc_TypeError, "%.200s() takes no arguments", type->tp_name);
            return NULL;
        }
    }

    if (type->tp_flags & Py_TPFLAGS_IS_ABSTRACT) {  // ② 拒绝实例化抽象类
        ... PyErr_Format("Can't instantiate abstract class %s ...") ...
        return NULL;
    }

    PyObject *obj = type->tp_alloc(type, 0);    // ③ ★委托 tp_alloc 分配内存
    if (obj == NULL) {
        return NULL;
    }
    return obj;
}
```

**伪代码概括**：`检查参数 → 检查抽象类 → tp_alloc 分配 → 返回`。总共 ~15 行。
注意它不直接 `malloc`，而是委托给类型自己的 `tp_alloc` 槽位（默认是 `PyType_GenericAlloc`）。

---

## 5. `type.__init__` 源码 —— 也基本不干活（行 3383）

```c
static int
type_init(PyObject *cls, PyObject *args, PyObject *kwds)
{
    assert(args != NULL && PyTuple_Check(args));
    assert(kwds == NULL || PyDict_Check(kwds));

    if (kwds != NULL && PyTuple_GET_SIZE(args) == 1 &&
        PyDict_GET_SIZE(kwds) != 0) {
        PyErr_SetString(PyExc_TypeError,
            "type.__init__() takes no keyword arguments");
        return -1;
    }

    if ((PyTuple_GET_SIZE(args) != 1 && PyTuple_GET_SIZE(args) != 3)) {
        PyErr_SetString(PyExc_TypeError,
            "type.__init__() takes 1 or 3 arguments");   // ← 允许 1 或 3 参数
        return -1;
    }

    return 0;   // 然后就...没了
}
```

**伪代码概括**：和 `object_init` 一样只校验参数，`return 0`。真正初始化类的活全在 `type_new` 里干完了。

---

## 6. `type.__new__` 源码 —— 造类工厂流水线（~838 行）

这是元类能控制「类怎么被造出来」的根源。整个流程分 8 个阶段：

```
class Dog(Base): ...            ← 解释器最终调用 type_new
│
├─ 阶段0  type_new          (行4261)  解析 3 参数: name/bases/dict
├─ 阶段1  type_new_impl     (行4148)  总编排，依次调下面 6 步
│        ├─ type_new_init           (行4111)  复制 dict、分配内存
│        ├─ type_new_set_attrs      (行4030)  写名字/模块/文档
│        ├─ PyType_Ready            (行8252)  ★算 MRO + 从基类继承所有槽位
│        ├─ fixup_slot_dispatchers  (行10705) ★把 def __add__ 挂到 C 槽位 nb_add
│        ├─ type_new_set_names      (行10740) 调描述符的 __set_name__
│        └─ type_new_init_subclass  (行10786) 调 super().__init_subclass__()
└─ 返回全新的类对象 Dog
```

### 阶段 0：入口 `type_new` —— 解析 3 参数（行 4261）

```c
type_new(PyTypeObject *metatype, PyObject *args, PyObject *kwds)
{
    /* 解析参数: "UO!O!" 表示
       U  = name   (必须是 str)
       O! = bases  (必须是 tuple)
       O! = dict   (必须是 dict)  */
    PyObject *name, *bases, *orig_dict;
    if (!PyArg_ParseTuple(args, "UO!O!:type.__new__",
                          &name,
                          &PyTuple_Type, &bases,
                          &PyDict_Type, &orig_dict))
        return NULL;   // ← 这就是报 "takes exactly 3 arguments" 的地方

    type_new_ctx ctx = { .name=name, .bases=bases, .orig_dict=orig_dict, ... };

    type_new_get_bases(&ctx, &type);   // 确定基类是谁，校验元类冲突
    type = type_new_impl(&ctx);        // ← 进入主流程
    return type;
}
```

**伪代码**：检查参数合法吗？基类是哪个？好，交给 `type_new_impl`。

### 阶段 1：总编排 `type_new_impl` —— 6 步流水线（行 4148，理解全局最关键）

```c
type_new_impl(type_new_ctx *ctx)
{
    PyTypeObject *type = type_new_init(ctx);        // ① 分配内存 + 准备 dict
    if (type_new_set_attrs(ctx, type) < 0) goto error; // ② 写名字/模块/文档/基类
    if (PyType_Ready(type) < 0) goto error;         // ③ ★算MRO、继承父类的所有槽位
    fixup_slot_dispatchers(type);                   // ④ ★把Python方法挂到C槽位
    if (type_new_set_names(type) < 0) goto error;   // ⑤ 调 __set_name__
    if (type_new_init_subclass(type, ctx->kwds) < 0) goto error; // ⑥ 调 __init_subclass__
    return (PyObject *)type;                        // ⑦ 交出成品：一个新类
}
```

**伪代码概括**：`分配 → 填名字 → 算继承 → 挂方法 → 回调钩子 → 出厂`。

### 阶段 2（步骤①）：`type_new_init` —— 分配内存（行 4111）

```c
type_new_init(type_new_ctx *ctx)
{
    PyObject *dict = PyDict_Copy(ctx->orig_dict);   // ①复制类的命名空间(别动用户的dict)
    if (type_new_get_slots(ctx, dict) < 0) goto error; // 收集 __slots__
    if (type_new_slots(ctx, dict) < 0) goto error;     // 处理 __slots__ 声明
    PyTypeObject *type = type_new_alloc(ctx);          // ②真正分配类型对象的内存
    set_tp_dict(type, dict);                           // 把命名空间挂到 tp_dict
    et->ht_slots = ctx->slots;                         // 记下 __slots__
    return type;
}
```

> 对比 `object_new` 只调一句 `tp_alloc`；这里多了「复制命名空间、处理 `__slots__`」——因为类要装一大堆方法和属性。

### 阶段 3（步骤③）：`PyType_Ready → type_ready` —— **继承核心（最重要）**

`PyType_Ready`（行 8252）只是个加锁包装，真活在 `type_ready`（行 8174）。**这一步解释了「为什么子类能继承父类」**：

```c
type_ready(PyTypeObject *type, int initial)
{
    if (type_ready_pre_checks(type) < 0) goto error;
    if (type_ready_set_dict(type) < 0) goto error;     // 初始化 tp_dict
    if (type_ready_set_base(type) < 0) goto error;     // 记下 tp_base（直接基类）
    if (type_ready_set_type(type) < 0) goto error;
    if (type_ready_set_bases(type, initial) < 0) goto error;
    if (type_ready_mro(type, initial) < 0) goto error; // ★算 MRO(方法解析顺序)
    if (type_ready_set_new(type, initial) < 0) goto error;
    if (type_ready_fill_dict(type) < 0) goto error;
    if (initial) {
        if (type_ready_inherit(type) < 0) goto error;  // ★从 MRO 里每个基类继承槽位
        ...
    }
    type->tp_flags |= Py_TPFLAGS_READY;   // 盖章：类已就绪
    return 0;
}
```

`type_ready_inherit`（行 7977）就是「继承」的真正发生地——遍历 MRO，把每个祖先的能力拷到新类：

```c
type_ready_inherit(PyTypeObject *type)
{
    PyObject *bases = type->tp_mro;
    Py_ssize_t nbase = PyTuple_GET_SIZE(bases);
    for (i = 1; i < nbase; i++) {            // 遍历 MRO 里所有祖先
        b = PyTuple_GET_ITEM(bases, i);
        if (inherit_slots(type, (PyTypeObject *)b) < 0)   // ★把祖先的槽位拷过来
            return -1;
    }
    type_ready_inherit_as_structs(type, base);
    return 0;
}
```

> **「子类拥有父类能力」的物理来源**：`type_ready` 算出 MRO，然后 `inherit_slots`（行 7492）沿着 MRO 把每个祖先的 C 槽位（`tp_repr`、`tp_hash`、`tp_richcompare`…）逐个拷到子类。你写的 `class Dog(Animal)` 之所以能调父类方法，本质就是这里把槽位复制了一份。

### 阶段 4（步骤④）：`fixup_slot_dispatchers` —— **Python 方法挂到 C 槽位**（行 10705）

这一步最「魔法」：你写的 `def __add__` 是 Python 函数，但 `a + b` 走的是 C 层的 `tp_as_number->nb_add` 槽位。两者怎么对上？就在这里：

```c
fixup_slot_dispatchers(PyTypeObject *type)
{
    BEGIN_TYPE_LOCK();
    for (pytype_slotdef *p = slotdefs; p->name; ) {   // 遍历"槽位定义表"
        p = update_one_slot(type, p);                 // 看你的 dict 里有 __add__ 吗?
    }                                                 // 有 → 把 nb_add 指向它
    END_TYPE_LOCK();
}
```

> `slotdefs` 是一张映射表：`{"__add__" → nb_add, "__eq__" → tp_richcompare, "__len__" → mp_length, ...}`。`update_one_slot` 检查你的类命名空间里有没有 `__add__`，有就把对应的 C 槽位接到这个 Python 函数上。**这就是为什么你写 `def __add__`，`+` 运算符立刻生效**——CPython 在造类时就帮你「接线」了。

### 阶段 6（步骤⑥）：`type_new_init_subclass` —— 调 `__init_subclass__`（行 10786）

这是给父类的「子类创建通知」钩子：

```c
type_new_init_subclass(PyTypeObject *type, PyObject *kwds)
{
    // 构造 super() 对象
    PyObject *super = PyObject_Vectorcall(&PySuper_Type, args, 2, NULL);
    // 拿到 super().__init_subclass__  ← 注意是 super，跳过当前类自己
    PyObject *func = PyObject_GetAttr(super, &_Py_ID(__init_subclass__));
    // 调用它，传入 class 语句里的关键字参数
    PyObject *result = PyObject_VectorcallDict(func, NULL, 0, kwds);
    return 0;
}
```

> 这一步等价于执行了 `super().__init_subclass__(**kwds)`。所以你在父类定义 `def __init_subclass__(cls)`，每当有子类被创建就会自动触发——不需要子类写 `super()`，CPython 在造类末尾替你调了。

---

## 7. 完整对比表

| | `object.__new__` | `type.__new__` |
|---|---|---|
| C 函数 | `object_new`（行 6107） | `type_new` 一族（入口行 4261） |
| 源码规模 | ~15 行 | ~838 行 |
| 干的活 | 检查参数→拒绝抽象类→`tp_alloc` 分配 | 分配→设属性→算 MRO→继承槽位→挂描述符→回调钩子 |
| 造出来的是 | 一个普通**实例** | 一个**类对象** |
| | `object.__init__` | `type.__init__` |
| C 函数 | `object_init`（行 6087） | `type_init`（行 3383） |
| 干的活 | 检查参数→`return 0`（啥也不做） | 检查参数（1或3个）→`return 0`（啥也不做） |
| 注册在 | `PyBaseObject_Type.tp_init` | `PyType_Type.tp_init` |

---

## 8. 调用链串联：你写 `class Dog(Base): ...` 时发生了什么

```
class Dog(Base): ...            ← 解释器遇到 class 语句
  → 调用元类的 __call__，即 type.__call__ = type_call（行 1940）
       → type.__new__(type, 'Dog', (Base,), {命名空间})
            = type_new(...)      ← 那 ~838 行的引擎在这里跑
              → type_new_impl: 算 MRO → 继承 object 的所有槽位
                              → 把你的方法挂到 C 槽位 → 调 __init_subclass__
              → 返回全新的类对象 Dog
       → type.__init__(Dog, ...)
            = type_init(...)     ← 只校验参数，return 0
  → 返回 Dog
```

而创建普通实例 `Dog()` 时：

```
Dog()
  → type.__call__(Dog) = type_call（行 1940）
       → Dog.__new__(Dog)   [tp_new 槽 → object_new，~15 行]
            → tp_alloc(Dog, 0) → 真正的内存分配，引用计数初始化
            → 返回新实例 obj
       → Dog.__init__(obj)  [tp_init 槽 → object_init 或你重写的版本]
            → 基类啥也不做；你的子类才填属性
  → 返回 obj
```

---

## 9. 附：`type.__call__` 的「一参数特例」（行 1940）

顺便解释一个相关疑问：为什么 `type(42)` 能查类型，而元类子类 `MyMeta(42)` 不行？

```c
type_call(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyTypeObject *type = (PyTypeObject *)self;

    /* Special case: type(x) should return Py_TYPE(x) */
    /* We only want type itself to accept the one-argument form (#27157) */
    if (type == &PyType_Type) {                        // ← 关键：精确相等
        Py_ssize_t nargs = PyTuple_GET_SIZE(args);
        if (nargs == 1 && ...) {
            obj = (PyObject *) Py_TYPE(PyTuple_GET_ITEM(args, 0));
            return Py_NewRef(obj);                     // ← type(x) 走这里
        }
        if (nargs != 3) {
            PyErr_SetString(PyExc_TypeError, "type() takes 1 or 3 arguments");
            return NULL;
        }
    }
    // 子类（MyMeta）跳过上面特例，直接走普通造类流程
    obj = type->tp_new(type, args, kwds);
    ...
}
```

注释里写明：**「我们只想让 `type` 本身接受一参数形式」**。门卫是 `if (type == &PyType_Type)`——指针级精确相等，子类通不过。

所以「查类型」从来不是 `type` 的可继承能力，只是 C 源码里写死给 `type` 本人的特权分支。「造类」（3 参数走 `tp_new`）才是通用机制，元类能继承。

---

## 10. 一句话总结

- **`__new__`/`__init__` 不是函数，是 C 槽位的「门面」**（包着 C 函数指针的可调用描述符）。
- **`object.__new__`** 的活是分配一块空内存；**`object.__init__`** 在基类里就是没活。
- **`type.__new__`**（~838 行）= 造类工厂流水线：解析 `(name, bases, dict)` → 分配 → 写属性 → **算 MRO 并沿 MRO 拷贝祖先槽位（继承的物理本质）** → **把你的 `__add__`/`__eq__` 接到 C 槽位上** → 回调 `__set_name__`/`__init_subclass__` → 出厂。
- **重写元类的 `__new__`**，就是在 `type_new_impl` 这条流水线外面套一层自己的壳，插手类的创建过程——这就是元类能控制「类怎么被造出来」的底层原因。

---

## 11. `type_new_impl` 读源码 / 用的注意事项（避坑指南）

`type_new_impl`（行 4148）只有十几行，但**步骤顺序、错误处理、时机**全是坑点。下面分「源码层面」和「行为层面」两块。

### 精确版源码（带完整注释，含文档第 6 节里省略的细节）

```c
type_new_impl(type_new_ctx *ctx)
{
    PyTypeObject *type = type_new_init(ctx);          // ① 分配
    if (type == NULL) return NULL;                    //   ← 用 NULL 判错

    if (type_new_set_attrs(ctx, type) < 0) goto error;// ② 写属性  (<0 判错)

    /* Initialize the rest */
    if (PyType_Ready(type) < 0) goto error;           // ③ MRO+继承 (<0 判错)

    // Put the proper slots in place
    fixup_slot_dispatchers(type);                     // ④ 接槽位 ★void，不判错!

    if (!_PyDict_HasOnlyStringKeys(type->tp_dict)) {  // ★藏在④⑤之间的检查
        if (PyErr_WarnFormat(RuntimeWarning, 1,
                "non-string key in the __dict__ of class %.200s") == -1)
            goto error;
    }

    if (type_new_set_names(type) < 0) goto error;     // ⑤ __set_name__ (<0 判错)

    if (type_new_init_subclass(type, ctx->kwds) < 0)  // ⑥ __init_subclass__ (<0 判错)
        goto error;

    assert(_PyType_CheckConsistency(type));           // ★调试断言

    return (PyObject *)type;

error:
    Py_DECREF(type);                                  // ★半成品类被销毁
    return NULL;
}
```

### 源码层面的注意事项

**注意事项 1：步骤顺序是刻意的，不能换**

源码注释 `/* Initialize the rest */` 和 `// Put the proper slots in place` 暗示了顺序逻辑：

- `③ PyType_Ready(算MRO+继承)` 必须先于 `④ fixup_slot_dispatchers(接你的方法)`
  ——因为 ④ 要把**你写的** `__add__` 接到 C 槽位上，前提是 ③ 已经把**继承来的**槽位铺好了，你的才能「覆盖」它们。换顺序，继承就接不上去。
- `⑤ __set_name__` 必须先于 `⑥ __init_subclass__`
  ——描述符先知道自己的名字，父类的 `__init_subclass__` 才被通知。这样父类看到的是一个「描述符都已就位」的成品。

**注意事项 2：`fixup_slot_dispatchers` 是唯一不检查错误的步骤**

| 步骤 | 返回类型 | 判错方式 |
|------|---------|---------|
| ① type_new_init | `PyTypeObject*` | `== NULL` |
| ② type_new_set_attrs | `int` | `< 0` |
| ③ PyType_Ready | `int` | `< 0` |
| **④ fixup_slot_dispatchers** | **`void`** | **❌ 不判错** |
| ⑤ type_new_set_names | `int` | `< 0` |
| ⑥ type_new_init_subclass | `int` | `< 0` |

源码 `typeobject.c:3208` 声明 `static void fixup_slot_dispatchers(...)`。它的内部注释也说「update_one_slot can't actually fail」。所以**槽位接线被假设永远不会失败**——这是个设计上的不对称，读代码时容易忽略。

**注意事项 3：中间藏着一个「字符串键」检查**

④ 和 ⑤ 之间夹着 `_PyDict_HasOnlyStringKeys`——类的 `tp_dict` 不允许非字符串键，否则给 `RuntimeWarning`。这是为什么类体语法层面根本不让你写 `123 = "x"`（直接 SyntaxError），用 `type()` 传非字符串键也会被警告。

**注意事项 4：末尾的 `_PyType_CheckConsistency` 是调试断言**

`assert(...)` 只在 **debug 构建**的 CPython 里生效，发行版被跳过。它做内部一致性自检（槽位、MRO 等没坏）。读源码时看到 assert 要知道：它不是运行时逻辑，是开发期的安全网。

**注意事项 5：失败即丢弃半成品**

`error:` 标签下 `Py_DECREF(type); return NULL;`——**任何一步失败，已经分配、部分建好的类被直接销毁**，对外表现为「这个类从没存在过」。见下面坑 2 的实证。

### 行为层面：这些源码细节导致的 Python「坑」

**坑 1：`__init_subclass__` 在造类时跑，不是造实例时**

很多人以为它和 `__init__` 类似，其实它在 `class` 语句执行的瞬间（步骤⑥）就跑了，而且只跑一次：

```python
class StrictBase:
    def __init_subclass__(cls):
        if cls.__name__ != "Allowed":
            raise ValueError(f"不让创建 {cls.__name__}")

try:
    class Forbidden(StrictBase):   # ← __init_subclass__ 在 ⑥ 步抛异常
        pass
except ValueError as e:
    print("类创建失败:", e)
# Forbidden 这个名字根本没绑定成功 → NameError: Forbidden 不存在
```

**坑 2：`__init_subclass__` 抛异常 → 整个类创建失败**

接坑 1——因为步骤⑥失败走 `goto error → Py_DECREF`，半成品类被销毁，`Forbidden` 从未存在。

**坑 3：`__init_subclass__` 收到的是「已成型」的类**

到步骤⑥时，③④⑤都跑完了——MRO 算好了、方法接到槽位了、`__set_name__` 也调过了。所以父类的 `__init_subclass__` 拿到的是一个**几乎完工**的类，可以读取甚至修改它：

```python
class Base:
    def __init_subclass__(cls):
        cls.added_by_parent = "我是父类塞的"   # ← 能改这个刚造好的类

class Child(Base):
    pass
print(Child.added_by_parent)   # 我是父类塞的
```

**坑 4：类在管线中途就已经「存活」，但出厂前不可见**

从步骤①分配内存起，这个类对象就存在了。到⑤⑥时，它能被 `__set_name__(owner=cls)` 和 `__init_subclass__(cls)` 拿到。**但它在 `return` 之前，对程序其他部分是不可见的**（`fixup_slot_dispatchers` 的注释明说 "the type has not been exposed to anyone else yet"）。所以这些钩子是「在类出厂前最后插手」的机会。

**坑 5：顺序决定了你「能依赖什么」**

因为 ③（继承）在 ⑥（`__init_subclass__`）之前，所以你在 `__init_subclass__` 里能放心用 `super()`、能读到继承来的方法——它们早就位了。如果顺序反了，父类通知时会拿到一个「还没继承好」的残次品。

**坑 6：步骤顺序可观测 —— `__set_name__` 先于 `__init_subclass__`**

实测：

```python
order = []
class Desc:
    def __set_name__(self, owner, name):
        order.append(f"__set_name__(name={name!r})")
class Base:
    def __init_subclass__(cls, **kw):
        order.append(f"__init_subclass__({cls.__name__})")
class Child(Base):
    x = Desc()

print(order)   # ['__set_name__(name=\'x\')', '__init_subclass__(Child)']
# → 造类时 __set_name__ 先跑，__init_subclass__ 后跑（源码 ⑤在⑥前）
```

### 总表

| 类别 | 注意事项 | 后果 |
|------|---------|------|
| 源码 | ⑥步顺序刻意 | 解释了 `__set_name__`/`__init_subclass__` 的触发次序 |
| 源码 | ④是 void，不判错 | 槽位接线被假设永不出错 |
| 源码 | ④⑤间藏字符串键检查 | 类 dict 不能有非字符串键 |
| 源码 | 失败 → `Py_DECREF` | 半成品类被销毁，类「从未存在」 |
| 行为 | `__init_subclass__` 造类时跑 | 抛异常→类创建失败 |
| 行为 | `__init_subclass__` 拿到成品类 | 父类可读/改刚造好的子类 |
| 行为 | 类出厂前对其他代码不可见 | 钩子是「出厂前最后插手」的机会 |

> **一句话**：`type_new_impl` 像一条「**严格按序、任一失败即报废**」的流水线——顺序解释了 Python 的很多行为（`__set_name__` 先于 `__init_subclass__`、继承先于方法接线），失败处理决定了「类要么完整诞生、要么从没存在过」，没有中间态。
