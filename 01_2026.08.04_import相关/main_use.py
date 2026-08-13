import show
import show_2
import show_folder.show_3 as show_3

def all_hello_show():

    show.hello_show()

    print('--------------------------')

    show_2.hello_show()

    print('--------------------------')

    show_3.hello_show()

if __name__ == '__main__':
    print(show.__dict__)
