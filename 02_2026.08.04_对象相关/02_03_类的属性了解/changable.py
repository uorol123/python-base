class Tdproject:
    # 类属性
    todolist:list[str] = []
    named: str = 'td'
    # 和实例属性同名
    name:str = 'tdd'
    # 实例属性
    def __init__(self,name):
        self.name = name
    def getName(self):
        return(self.name)
    def getName2(self):
        return(self.named)

def show_attrs(obj):
    cls = type(obj)
    print("--- 实例属性 ---")
    for k, v in vars(obj).items():
        print(f"  {k} = {v!r}")
    print("--- 类属性 ---")
    seen = set(vars(obj))
    for k in dir(cls):
        if k in seen or k.startswith("__"):
            continue
        v = getattr(cls, k)
        print(f"  {k} = {v!r}")

me = Tdproject("me")
you = Tdproject("you")

print(me.todolist)
print()
you.todolist.append("stay")
print(me.todolist)
print()

# 看看这个Tdproject是个啥
show_attrs(me)
print()
print(me.__dict__)
print()
print(me.__hash__)

# 看一下函数
print('---2----')
print(me.getName())
print('-------')
print(me.getName2())

# 改一下类属性
you.named = 'td_New'
you.name = 'tdd_New'

print('---3----')
show_attrs(me)
# 从后续打印可以发现you.name 和named没有动到类，而且给you的dict新增了两个实例属性
print('---4----')
show_attrs(you)
print('---5----')
print(you.__dict__)
