# 前提
1. Python 里万物皆对象
2. 类（class）也是对象
3  type 可以用来查类型也可以用来造类：
    print(type(42)) # <class 'int'>
    Dog = type('Dog', (), {}) # ← 动态造了一个空类
    print(Dog)               # <class '__main__.Dog'>

## type是什么
type在 `/home/ubuntu/projects/pythonStudy\python_base/02_2026.08.04_对象相关/from_object/readme.md` 我就了解过，
type 是实例树的根，是继承了object的类，type有两个作用，一个是查类型，一个就是造类

```python
type(
    'Dog',      # 参数1：要造的类的名字（字符串）
    (),         # 参数 2：父类们（元组），这里是空 =继承 object
    {}          # 参数 3：类的属性字典，{'x': 1} 这种)
```
**演示： type_use.py**

所有的 class 语句，底层都是 type(...) ,用class可读性更好，class是保留的关键字，是type的语法糖

> **GPT 修正**：`type(...)` 只是在“默认元类 + 普通命名空间”场景下便于理解的近似。严格流程是 `__build_class__ → 选择元类 → metaclass.__prepare__ → 执行类体 → 调用元类`，最终元类可能是 `type` 的子类而不是 `type` 本身。
TODO：type和object的源码阅读


# 什么是元类

元类 = 用来造类的类。
1.type 是 Python 默认的元类
2. 任何一个"继承 type 的类"都是元类。
3.因为元类继承了type，所以可以通过元类来造类

## 和基类的区别
基类和继承类似，元类和类型类似。 而元类就是继承自type的类（直接继承），别忘了type也是个类，是object

每个类都继承或者间接继承自object（基类），类型都是或者间接是type(元类)

## 问题
Metaclass_example.py：
class MyMeta(type) 里既继承 type、又被 type 造——这个"递归"是怎么没炸的？
type 自己（默认元类）它的 __bases__ 是什么？它的 type 又是什么？
能不能写一个"自己造自己"的元类？链条会无限下去吗？


## 继承type的问题
Metaclass_example.py 能看到，MyMeta可以用来造（new创建和init初始化一个类），但是不能用来查询类型。
这是因为：
「参数查类型」这个能力，是 CPython 源码里给 type 本尊写死的特例，根本不是 type 的通用能力，所以子类继承不到。 而「造类」是 tp_new/tp_init 这些通用机制，子类能正常继承。

看 Objects/typeobject.c:1953-1973 的 type_call 函数：
```
  /* Special case: type(x) should return Py_TYPE(x) */
  /* We only want type itself to accept the one-argument form (#27157) */
  if (type == &PyType_Type) {                              // ← 关键这一行,我的元类这里不等于type（地址不同）
      Py_ssize_t nargs = PyTuple_GET_SIZE(args);
      if (nargs == 1 && ...) {
          obj = (PyObject *) Py_TYPE(PyTuple_GET_ITEM(args, 0));
          return Py_NewRef(obj);                            // ← type(x) 查类型，走这里
      }
      if (nargs != 3) {
          PyErr_SetString(PyExc_TypeError,
                          "type() takes 1 or 3 arguments");
          return NULL;
      }
  }
```
  // ↓ 如果上面 if 没进（比如 MyMeta），就走普通造类流程:
  obj = type->tp_new(type, args, kwds);                    // ← 调 __new__ 造对象
  
# 自定义的元类可以用来做什么

在类被"造出来"那一刻插入代码
