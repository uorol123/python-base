class D:

    def __get__(self, instance, owner):
        return "descriptor"

    def __set__(self, instance, value):
        instance.__dict__["x"] = value


class A:
    x = D()


a = A()

a.__dict__["x"] = "instance"

print(a.x)
