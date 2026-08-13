class MyMeta(type):   # 继承 type → MyMeta 是个元类。简单来说就是指定基类为type，继承了type的特性。
    pass

class Dog(metaclass=MyMeta):   # 让 MyMeta 来造 Dog
    pass

print(type(Dog))         # <class '__main__.MyMeta'>   ← Dog 的元类变成了 MyMeta

# 问题： 既然继承了type，那么type的查询类型和造类的能力也有了吗？

# 实际测试
Foo = MyMeta('Foo', (), {'x': 1})
print(Foo, Foo.x) # <class '__main__.Foo'> 1
try:
    print(MyMeta(42))
except TypeError as e:
    print(e) # type.__new__() takes exactly 3 arguments (1 given)

print("-----------------------------------------------")

class MyMeta(type): # 干净的 MyMeta，没覆盖 __call__
    pass

print(MyMeta.__call__)              # <slot wrapper '__call__' of 'type' objects>
print(MyMeta.__call__.__qualname__) # 'type.__call__'


print("----------------part II -----------------")
class MyMeta(type):
    def __new__(mcs, name, bases, namespace):
        print(f"[元类 __new__] 正在造类: {name}")
        cls = super().__new__(mcs, name, bases, namespace)
        # mcs       : 这个元类自己（这里是 MyMeta）
        # name      : 'Dog'              ← 类的名字
        # bases : (<class 'object'>,) ← 基类们
        # namespace : {'__qualname__': 'Dog', ...} ← 类体里的所有属性
        print(f"[元类 __new__] 类造好了: {cls}")
        return cls


class Dog(metaclass=MyMeta):   # ← 这一行执行时，MyMeta.__new__ 会跑 pass
    pass
print("Dog 这个名字:", Dog)
