# type继承自object

object是所有类的最终祖先，object本身有type
type是所有类型的最终祖先，type本身就是类

# 关键信息
object.__new__ / object.__init__ 是包着 C 函数指针的「可调用描述符」

object 和 type 在 C 里都是一张巨大的结构体表，每个字段叫一个**「槽位 (slot)」**。访问 xxx.__new__ 时，类型系统从 tp_new 槽位里把那个 C 函数指针包成一个描述符交给你。

type 这个结构体里 tp_init/tp_new/tp_call 全是 type_* 版本——这就是「重写」在 C 的表达，所以
type 的 __new__ , __init__(这个看子类) ， __call__ 和object是不一样的

# 阶段

## 阶段0  type_new    解析 3 参数: name/bases/dict
`test_args_new.py`

| 参数 | 是什么 | 类型 | 类语句里的对应 | 找完后在哪看 |
| --- | --- | --- | --- | ---|
| name | 类名 | str | class 名字 | 类.__name__ |
| bases | 父类们 | tuple | (父类1, 父类2) | 类.__bases__ |
| dict | 命名空间(成员表) | dict | 类体里的所有赋值/函数 | 类.__dict__  |

## 阶段 1：总编排 type_new_impl —— 6 步流水线（行 4148，理解全局最关键）

这个过程比较繁琐，直接看ai总结流程。

## 注意事项

class A（） 和 A（）的区别
刚刚知道，object也是有__init__ 和 __new__ 的

通过这些步骤，类就被创建好了
