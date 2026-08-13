from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
    quantity: int = 0  # 可以有默认值

# 如果没有
class Product2:
    def __init__(self,name,price,quantity,prolist,*args):
        self.name = name
        self.price = price
        self.quantity = quantity
        for i in args:
            print(f"{i} is not acceptable")

if __name__ == '__main__':
    # 实例化一个
    p1 = Product('uh',2.2,5)
    print("---------part I -------")
    print(p1) # Product(name='uh', price=2.2, quantity=5)

    p2 = Product2('uh',2.2,5,[1,2,3,4])
    print("-----------------")
    print(p2) #<__main__.Product2 object at 0x7f71d7189ee0> ,可以看到打印区别明显

    print("-----------比较equal------------")
    p3 = Product('uh',2.2,5)

    print(p1 == p3) # True
    # False
    print(p2 == p3)
    # 这里有个 == 的小知识，默认情况下，会先调用左侧对象的__eq__ 做比较，
    # 当该方法返回 NotImplemented，比如这里p1和p2的type：Product1和Product2不一致，不比较。然后再用右边的__eq__方法，p2的type:Product2没定义，Product2的父类object：
    # 两边都返回 NotImplemented → 回退到 is（身份比较）→ 不同对象 → False
    print(p1 == p2)
    print(p2 == p1)


    print("---------part II -------")
    print()
    # 但是注解更像是约定，而非范式，就像_name 一样
    p4 = Product(1,2,3)

    print(p4) #Product(name=1, price=2, quantity=3) ,依然有效
