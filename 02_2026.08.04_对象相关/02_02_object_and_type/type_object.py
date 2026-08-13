# —— 三层四个事实，把整个 Python 对象模型说清 ——

print(type.__bases__)        # 1) type 继承自 object
# (<class 'object'>,)

print(object.__bases__)      # 2) object 没有父类，是根
# ()

print(type(object))          # 3) object 是 type 的实例
# <class 'type'>

print(type(type))            # 4) type 是 type 自己的实例（自指）
# <class 'type'>


a = 1
b = "hi"
c = [1, 2]
d = {a:2}
e = 2000
f = 111.422

for x in [a, b, c,d,e,f]:
    print(f"{type(x).__name__} 的祖先链：", type(x).__mro__)

c1 = [1,2]
c2 = c

c2.append(3)
c1.append(4)

print(c," ",c1, " ",c2)  # [1, 2, 3]   [1, 2, 4]   [1, 2, 3]。c2 = c = <[1,2]>.而c1自己实例化了新的 list类。

a1 = 0
a2 = a
print(a is a2) # True
print(a," ",a1, " ",a2) # 1   0    1 。从c的角度来看，a似乎应该和a2 一样等于2，但是实际上 小整数是缓存，永远是同一个对象 。

e1 = 2000
e2 = e

print(e is e1) # True
print(e is e2) #True

f1 = 111.422
print(f is f1) # True
