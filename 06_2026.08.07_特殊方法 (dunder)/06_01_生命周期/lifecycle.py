"""
1. __init__(self, ...) — 初始化器（最常用）
    什么时候触发：创建实例 MyClass(...) 时。
    做什么： 啥也不做（直接返回 None）。需要我根据自己的对象去重写
2. __new__(cls, ...) — 真正"造对象"的工厂
    什么时候触发：__init__ 之前，负责创建并返回实例本身。__init__ 只负责"装填"已经造好的对象。
    做什么： 向内存申请一块空对象，类型标记为 cls，然后返回它。它只负责「生」，不填任何内容。
3.__del__(self) — 析构器（谨慎用）:
    什么时候触发：对象引用计数归零 / gc 回收时。本身object不存在

    Python 的垃圾回收器（gc 模块）在销毁对象前，会做一次特殊查找
    // CPython gcmodule.c（简化）
    tp_del = _PyType_Lookup(type(obj), "__del__");
    if (tp_del != NULL) {
        /* 调用用户的 __del__ */
    } else {
        /* 直接释放对象，不报错 */
    }

"""
class Trace:
    def __init__(self, x):
        print("我会被覆盖")

# 流程
class Trace:
    def __new__(cls, *args, **kwargs):
        print("① __new__ 跑：分配内存，造实例")
        obj = super().__new__(cls)
        print(f"   super().__new__(cls) 拿到的 id = {id(obj)}")
        return obj

    def __init__(self, x):
        print(f"② __init__ 跑：self.id = {id(self)}, 收到 x={x}")
# 上面这个是定义了一个类

# 这里是实例化
t = Trace(42)

# 实例化和定义一开始都先调用type.__call__ 不同的是 class Trace是通过 type.__new__被造出来 ， 通过type.__init__ 被初始化。
# 后续 Trace继承了object（或者其他父类）的 __new__和 __init__ ，t实例化时也会调用。
# 简单来说 class Trace 这段代码也是一个实例化的过程，不过 __new__和 __init__ 是通过type而产生的。（因此第一个Trace被第二个覆盖了）


# __new__ 的特殊用法

# 1. 不可变类型的子类（int / str / tuple），因为它们的字段在 __init__ 时已经设不了了
class MyInt(int):
    def __new__(cls, value):
        return super().__new__(cls, abs(value))   # 强制为正数

# 2. 单例，这个能实现单例是因为每个对象 实例化 这个类时都要走这个改写的__new__方法，而 _instance 是 类属性 ，创建时共享，不会重复创建实例。
class Singleton:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# 3. 元编程 / 元类里构造对象
# 请看：03_2026.8.6_元类学习/readme.md
