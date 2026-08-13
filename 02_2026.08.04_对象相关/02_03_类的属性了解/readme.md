--- 2026.08.07更新

# 对象定义的本质

在之前的学习中了解到，
clss XXX 定义了一个类后（无论是元类还是其他）：
```python
class A:
    xxx:

    def __new__(cls,xxx,*args,**kwargs):
        xxx
        return super().__new__(cls)
        # 03_2026.8.6_元类学习/01_logBeforeUse.py
        # 普通类：super().__new__(cls) → object.__new__(cls)，只传 cls，分配实例内存
        # 元类：super().__new__(cls, name, bases, namespace) → type.__new__，创建类对象
             

    def __init__(self,xxx,*args,**kwargs):
        slef.xxx = xxx
        xxx

# 实例化
a = A（xxx）
```
这个对象可以有自己的__init__ 和__new__，这个new里面需要使用super().__new__ 去真正在内存里创建一个对象。
## class本质和创建对象

class 是 type(str,tuple,dict) 的语法糖，而（）则代表去对象的类型（type）上寻找__call__ 并执行，type的类型就是其本身，所以会调用type.__call__,而type的__call__做的事情是：
调用 type.__new__ 和 type.__init__

本质都是通过 type.__new__ 和 type.__init__ 去在内存中创建（先有cls作为类型对象传给new去创建，然后type的init基本不做什么）。

注意，这里用的是type的__new__ 和 type的init，跟自己类里面怎么定义的无关。后续实例化才用的到：

## 实例化的本质
实例化的时候类似，A(xxx) ,本质也是去 A的type（A的type也是type），然后就会用type的__call__【这里也要注意，type的__call__是类型的方法，__call__执行时用的__new__和__init__】用的是A的__init__ 和__new__ ,，而不是type的。（后面通过type查询a的类型也会发现其属于__main__.A）

然后A由于没有指定type为父类（这里涉及元类，不展开），__new__的super本质上是调用 父类（object）的__new__ 【注意，只有元类才调用的是type的__new__】。所以只是创建了一个对象，分配空间。

# 为什么对象的属性分实例属性和类属性
基于之前的学习记录做出我的判断：
类属性是存储在 A.__dict__ 里的,A的xxx首先要是可变对象，不然无法通过实例修改，只能通过类A.xxx = 来重新赋值。
而 a.xxx = newX 是赋值操作，本质是往a.__dict__ 放新的元素。（这个__dict__就是一个字典）

假设a.named = '232'
是往a.__dict__  插入数据

可变对象（比如数组）修改：
本质是在先在 a.__dict__里查找该属性，这个在a里不存在，然后就通过a的type去查这个，拿到了就修改。否则就报错

类也是存储在内存中的。有自己的内部属性。

而a是实例化的 A。（从type和object的继承链和传承链角度就很好理解了，a的类型是A，代表着a有A的一些能力

## 同名的怎么处理


# 注意

**本质是在先在 a.__dict__里查找该属性，这个在a里不存在，然后就通过a的type去查这个，拿到了就修改。否则就报错。**

这个描述不是很正确，从Python 对对象的一切操作，都先去对象的 type 上找对应的方法出发，让ai写一个详细的说明文档：

04_2026.08.06_type/04_04_python的一切操作顺序/readme.md

大致情况是：
1.在type上的MRO里找到了（a的type是A，A.__dict__里有同名的name，但是这个name只是普通属性，不是`数据描述符`「 没有set和del」,加上也没有`__get__`,也不是普通修饰符），暂存
2.然后到a（本身）的__dict__找，也找到了（同名），优先级高于`非数据描述符` 的type(他的type是A),替换返回了本身的name.

情况补充：
name是__dict__的key，真实值分别是：'tdd' 和 'me' 他们也都是对象（这点很重要），然后他们的type是str，父类是object。没有__get__ ，__set__这些方法吗，所以不是修饰符或者数据修饰符。
另一个要注意的是：
不是说只有a.xxx 获取才走这个优先级，正如标题所说，一切python的操作顺序 + 万物皆对象，所以本质上一切属性都能设置成`数据描述符` 来让任何操作都优先级最高。

比如__set__ ,通过这个可以在设置值时走我自己预设的逻辑（不真设置该值，用默认值之类的），__del__则可以在删除时不删，或者做其他操作。

这个`数据描述符`依赖于python的这个优先级机制，是高度抽象的机制，需要仔细理解
