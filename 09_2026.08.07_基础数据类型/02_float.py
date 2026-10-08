from math import nan,inf

a = 1.5
b = a

if a is b:
    # 都指向 1.5
    print("a is b")
a += 1

print(f'a is {a}')

# 精度
n = 2**53 + 1
result = 1.0 + n
print(n)
print(result)

x =nan
from decimal import Decimal
print(Decimal('0.1') + Decimal('0.2') == Decimal('0.3'))
print(0.1+0.2 == 0.3)
# nan不等于nan
print(nan == nan)

print('-------------------hash比较-------------')
if hash(1) == hash(1.0):
    print(hash(1.0))

if 1 == 1.0:
    print('1 == 1.0')
if 1 is 1.0:
    print('1 is 1.0')
