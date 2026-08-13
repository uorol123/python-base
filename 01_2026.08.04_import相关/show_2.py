# 这里定义一个函数打印hello和__name__,但是我们在这里不直接调用,只有当__name__ 为main时才调用，与show相反.
def hello_show():
    print(f'hello show2 and {__name__}')

if __name__ == '__main__':
    hello_show()
