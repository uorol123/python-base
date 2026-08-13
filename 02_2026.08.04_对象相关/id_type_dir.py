a = 1000
b = int("1000")   # 值与 a 相等，但是另一个独立对象
print('=== 1. 身份 id() ===')
print(f'a 的 id : {id(a)}')
print(f'b 的 id : {id(b)}')
print(f'a is b  : {a is b}        ← False：两个名字指向两个不同的对象')
print(f'a == b  : {a == b}        ← True ：但它们的值相等')
print()


# ---------- 2. 类型 (type)：决定对象"能做什么" ----------
print('=== 2. 类型 type() ===')
print(f'type(a)       = {type(a)}')            # <class 'int'>
print(f'type("hello") = {type("hello")}')      # <class 'str'>
print(f'type([1,2])   = {type([1,2])}')        # <class 'list'>
print(f'type(print)   = {type(print)}')        # <class 'builtin_function_or_method'>
print(f'type(int)     = {type(int)}')          # <class 'type'>  ← 类型本身也是对象！
print()


int_abilities = [x for x in dir(int) if not x.startswith('_')]
print(f'int 能做的事（部分）: {int_abilities[:8]}')
print('  ↑ 这些都是 int 类型承诺给它的对象的能力，比如 .bit_length() .real 等')
print()
