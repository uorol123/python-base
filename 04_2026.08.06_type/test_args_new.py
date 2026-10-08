def pirnt_obj(obj:object):
    print(obj.__name__)
    print(obj.__bases__)
    print(obj.__dict__)
    print()

class Sample:
      count = 0              #  → {'count': 0}            值是 int
      name = "样本"          #  → {'name': '样本'}         值是 str
      def hello(self): pass  #  → {'hello': <function>}   值是 function
      class Inner: pass      #  → {'Inner': <class>}       值是 class

# 之前了解到 class是type的语法糖。这里实际就已经通过type的 __new__ 和 __init__ 来创建对象了
# GPT 修正：这是默认元类场景的近似。真实 class 语句先经过 __build_class__、
# 元类选择和 __prepare__，最后调用选定元类；该元类不一定是 type。
# 三个参数
#  name = Sample
# dict = {'count': 0,'name': '样本','hello': <function>,'Inner': <class>}（重复的class）
# bases = None, 没有父类，默认父类为 object

class Hello:
    name ='hello'

class Sample1(Sample):
      pass

class Sample2(Sample,Hello):
    pass

pirnt_obj(Sample)
'''
Sample
(<class 'object'>,)
{'__module__': '__main__', 'count': 0, 'name': '样本', 'hello': <function Sample.hello at 0x7892dcfa4ea0>, 'Inner': <class '__main__.Sample.Inner'>, '__dict__': <attribute '__dict__' of 'Sample' objects>, '__weakref__': <attribute '__weakref__' of 'Sample' objects>, '__doc__': None}
'''
pirnt_obj(Hello)
"""
Hello
(<class 'object'>,)
{'__module__': '__main__', 'name': 'hello', '__dict__': <attribute '__dict__' of 'Hello' objects>, '__weakref__': <attribute '__weakref__' of 'Hello' objects>, '__doc__': None}
"""
pirnt_obj(Sample1)
"""
Sample1
(<class '__main__.Sample'>,)
{'__module__': '__main__', '__doc__': None}
"""
pirnt_obj(Sample2)
"""
Sample2
(<class '__main__.Sample'>, <class '__main__.Hello'>)
{'__module__': '__main__', '__doc__': None}
"""



#查询一下
