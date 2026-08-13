class TraceMeta(type):
    """任何继承 Base 的类，每个方法被调用时都打印日志"""

    def __new__(mcs, name, bases, namespace, **kwargs):
        # 遍历 namespace，把每个可调用的属性包一层
        for attr_name, attr in list(namespace.items()):
            if callable(attr) and not attr_name.startswith("__"):
                namespace[attr_name] = TraceMeta._wrap(attr_name, attr)

        return super().__new__(mcs, name, bases, namespace, **kwargs)

    @staticmethod
    def _wrap(name, func):
        def wrapper(*args, **kwargs):
            print(f" → 调用 {name}")
            result = func(*args, **kwargs)
            print(f"  ← {name} 返回 {result!r}")
            return result
        return wrapper


class Base(metaclass=TraceMeta):
    pass


class Calculator(Base):
    def add(self, a, b):
        return a + b

    def mul(self, a, b):
        return a * b


c = Calculator()
c.add(2, 3)
c.mul(4, 5)
