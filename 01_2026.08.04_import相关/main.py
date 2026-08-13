# import show
import sys
# 这里打印一次
from show import hello_show
# 给变量hello_show重新赋值
# 等价于：import show_2 hello_show = module.hello_show
from show_2 import hello_show
from show_folder.show_3 import hello_show
from main_use import all_hello_show

if __name__ == '__main__':
    print(__name__)
    print('----')
    hello_show()
    #重新赋值
    hello_show = 2
    try:
        #名字—对象绑定（name binding）
        hello_show()
    except TypeError as e:
        print(hello_show)
        print(e)
    print('----')
    all_hello_show()
