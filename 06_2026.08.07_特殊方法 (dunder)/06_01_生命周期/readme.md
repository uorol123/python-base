关于生命周期，__new__ ,__init__ ,__del__ 这些知识在8月4号已经学习,type,object的__new__ 和 __init__ 以及类，元类、各种数据库类型的完整创建过程（销毁过程设计GC，还未系统学习） ，这里只把生命周期的做个归档

# __new__ 和 __init__

正常情况 → 只写 __init__。
单例 / 不可变子类 / 元类场景 → 才需要写 __new__，而且 return super().__new__(cls)。必不可少
// C层面的伪代码
```C
void* obj = (cls*)PyType_GenericAlloc(cls, 0);  // 给 cls 类型分配一块裸内存
return (PyObject*)obj;                          // 把这块内存包成对象返回
```
