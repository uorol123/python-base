# type和object的关系
- type_object.py

object 是继承树的根；type 是实例树的根。 它们俩互相成全，形成一个"自洽的闭环"，靠解释器在 C 层硬编码保证存在。

type 和 object 是 CPython 启动时在 C 层创建的：
```C
// CPython 启动序列（简化）
_PyRuntime_Init() {
    _PyTypes_Init();            // 初始化 type 系统
    _PyObject_Init(&_PyBaseObject_Type);  // ← object 在这里
    _PyType_Init(&_PyType_Type);          // ← type 在这里
}
```

> **GPT 修正**：上面的函数名和顺序应视为帮助理解的**伪代码**，不能当作 CPython 3.13 的可定位调用链。可确认的事实是 `PyType_Type`、`PyBaseObject_Type` 等静态类型对象由运行时启动流程完成 bootstrap；精确流程应以当前源码的 runtime/type 初始化函数为准。
任何一个 Python 对象 x：
纵向（继承轴）：object 一定在 type(x).__mro__ 里 → x 一定"间接继承自 object"
横向（实例轴）：type(type(...type(x)...)) 走到底一定是 type → x 一定是"type 这条生产线的产物"



## 衍生问题

Q:既然一切都最终来源于objct和type
那么下面这些操作是不是就是在进行实例化（type的实例化和object的继承int，str这些子类的进一步实例化呢）
```python
a = 1        # 等价于  a = int(1) ，小整数：缓存，永远是同一个对象，不会新建,就是说这个1已经被实例化过了，已经有内存空间了，无论a =1 或者 b =1 都只是指向，不会有新的 <1> 被创建
b = "hi"     # 等价于  b = str("hi") ，短字符串：通常 intern（驻留）。创建后会存在一段时间，被回收前如果 c = “hi”，指向的也是同一块内存地址
c = [1, 2]   # 等价于  c = list([1, 2]) ， 列表 / 字典 / 集合：每次必新建（mutable，不能共享）
d = {1: 2}   # 等价于  d = dict({1: 2})
e = 1.5      # 等价于  e = float(1.5) ，浮点数，每次新建，但是重复赋值时CPython 编译器把同一个文件里重复出现的字面量合并到了同一个常量对象
f = 10000    # 等价于  f = int(10000) , 大整数：每次新建,
```
A： = 从来不构造任何新对象——它只是把名字指向右边那个已经存在的对象。
B：实例化是在右边的字面量：Python 编译器在编译阶段就把字面量翻译成对应的"构造调用"了。所以从结果看，写 1 和写 int(1) 一样，都是实例化。

> **GPT 修正**：字面量不会被翻译成 `int(...)`、`str(...)` 之类的 Python 层构造调用。常量通常进入 code object 的常量表并由 `LOAD_CONST` 读取；列表、字典等使用专门字节码构建。`1` 与 `int(1)` 最终都得到 `int` 对象，但创建路径、缓存行为和可观察副作用不能据此视为完全等价。

> **GPT 修正（缓存边界）**：小整数缓存是 CPython 实现细节；字符串是否 intern 不能用“短字符串通常都会驻留”概括；同一 code object 中的大整数、float、字符串字面量还可能因常量表复用而共享身份。不要用 `is` 反推对象的通用创建规则。

## 举例说明定义和实例化的区别

情况 A：实例化 MyClass（造的是 "对象"）
    MyClass(args)
    = type.__call__(MyClass, args)          //这个__call__ 是固定调用的，当class A重名后，后者会覆盖前者。
                                            可以看看 ：《猴补丁（monkey patch）》 怎么"冻结"一个类，让它不能被 monkey patch？
    → MyClass.__new__(MyClass, args)        ← 拿实例
    → MyClass.__init__(obj, args)           ← 初始化实例

情况 B：定义 class Foo（造的是 "类"，类也是一种对象）
    class Foo: ...                          ← 等价于 type('Foo', (), {...})
    = type.__call__(type, 'Foo', (), {...})
    → type.__new__(type, 'Foo', (), {...})  ← 拿类对象
    → type.__init__(cls, 'Foo', (), {...})  ← 初始化类对象

> **GPT 修正**：这里是默认元类、无高级特性的近似模型。真实 `class` 语句会先执行 `__build_class__` 流程，包括解析基类、选择元类、调用 `metaclass.__prepare__`、执行类体、处理 `__classcell__`，最后才调用选定元类；该元类也不一定是 `type`。


## cls 和 self的区别

| 类别 | 属性 | 作用 |
|---|---|---|
|self|实例（对象）|普通实例方法的第一个参数|
|cls|类（类型对象）|__new__、@classmethod 的第一个参数,在self创建前存在|

## a = Myobject()的完整流程

MyClass(args)
    ↓实际触发的是 type.__call__(MyClass, args)
    ↓
    ├─ 1) 调用 cls.__new__(cls, args)        ← 拿到一个实例 obj
    │
    └─ 2) 如果 obj 是 cls 的实例
 → 调用 obj.__init__(args)           ← 在刚造好的 obj 上跑


一个没搞懂的问题：

@classmethod

class A:
    @classmethod
    def f(cls): return "first"

# 直接重新赋值会丢装饰
A.f = lambda cls: "second" # 变成普通函数了！
A().f()

这个到底是在做什么


# type和object的 __new__ 和 __init__

上文已经说明了 object和type都是对象，也是相互的闭环。
type继承自object， __new__ 和 __init__ 实际上object也有

type 重写了 __new__ 和 __init__，没用 object 那份。实证：
  type.__new__  is object.__new__  → False   ← 不同的 C 函数
  type.__init__ is object.__init__ → False
  '__new__'  in type.__dict__ → True         ← type 自己定义的，不是继承来的

简单总结：object.__new__ 是「造一个空壳」，type.__new__ 是「造一座完整的类」

详细：
`/python_base/04_2026.08.06_type和object/type的init和new_来自AI.md`
`/python_base/04_2026.08.06_type和object/type的new.md`
