a = bool([1])
b = bool("Python")
c = bool(999)

if a is b:
    print('a is b')
if b is c:
    print('b is c ')


# 判断顺序
class Demo:
    def __bool__(self):
        return False

    def __len__(self):
        return 100


obj = Demo()

if True:
    print('true')
if False:
    print('false')
if None:
    pirnt('None')
if obj:
    print('obj')

if Demo:
    print('Demo')

class Wrong:
    def __bool__(self):
        return 1

wrong = Wrong()

try:
    if wrong:
        print('wrong')
except TypeError as e:
    print(e)

try:
    x = not wrong
except TypeError as e:
    print(e)

result1 = [] or "default"

result2 = "ready" and 0

# 短路，右边不会被执行
result3 = 0 and print('123')
result33  = not 1
if []:
    print('123')
else:
    result333 = not []
    print(f"result not [] is {result333}")
print('-----------------------------------------------------------')
print(result1)
print(result2)
print(result3)
print(result33)
print('-------------------------& 和 and---------------------------')

# True进逻辑判断，
result4 = True & 3

result5 = True and 3

result6 = False & 4
result7 = False and 4

print(result4)
print(result5)
print(result6)
print(result7)
