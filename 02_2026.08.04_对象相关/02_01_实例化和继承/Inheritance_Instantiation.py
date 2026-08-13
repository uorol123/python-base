"""
继承和实例化，
Myobject是<class 'type'>
但是 my 是<class '__main__.Myobject'>

"""

class Myobject:  # type.__new__ 被调用 → 造出「类对象 Myobject」（内存里就这一份）
    pass

class My2object(Myobject):
    pass

my2 = My2object()
my = Myobject() # Myobject.__new__ 被调用 → 造出「实例对象 my」（每次调用各一块）

# 看看是什么
print(type(Myobject)) # <class 'type'>
print(type(my)) # <class '__main__.Myobject'>
print(type(My2object)) # <class 'type'>
print(type(my2)) # <class '__main__.My2object'>

print('-------------------------------------')
# 1.看看继承关系,三代继承关系
print(Myobject.__bases__)        # (<class 'object'>,)
print(My2object.__bases__)       # (<class '__main__.Myobject'>,)
print(issubclass(Myobject, object))  # True
print(issubclass(My2object, object))  # True

# 实例化
print(isinstance(my, Myobject))  # True
print(isinstance(my, object))    # True（间接通过 Myobject）
