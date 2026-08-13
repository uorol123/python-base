Dog = type('Dog', (), {'legs': 4, 'bark': lambda self: '汪!'})

d = Dog()
print(d.legs)            # 4
print(d.bark())          # 汪!

# 等价于
class Dog2:
    legs = 4
    def bark(self): return '汪!'

d2 = Dog2()
print(d2.legs)            # 4
print(d2.bark())          # 汪!

# type 是 Python 默认的元类
class Dog3:
    pass

print(type(Dog3))         # <class 'type'>   ← Dog 的元类是 type


class A:
    pass
print("A.__bases__ =", A.__bases__)   # (<class 'object'>,)     ← 父类
print("type(A)    =", type(A))          # <class 'type'>          ← 元类
print("A 是 type 的子类?", issubclass(A, type))  # False
print("A 是 object 的子类?", issubclass(A, object))  # True

# 对比自定义元类
class MyMeta(type):
    pass

print("MyMeta.__bases__ =", MyMeta.__bases__) # (<class 'type'>,)   ← 父类是 type
print("type(MyMeta)    =", type(MyMeta))      # <class 'type'>      ← 元类还是 type（递归）
print("MyMeta 是 type 的子类?", issubclass(MyMeta, type))  # True ✅
