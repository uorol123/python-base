### int
int是不可变对象，不会像c语言一样溢出，真正存储的是C里的数组;当数字过大时会自动扩展数组，存储值更大的数字。
每个 digit 是 32 位无符号整数，但只用其中 30 位存数据（留 2 位给进位/符号处理）

 GPT 修正（CPython 3.13）：
struct _longobject { PyObject_HEAD; _PyLongValue long_value; };
_PyLongValue = { uintptr_t lv_tag; digit ob_digit[1]; }
digit 数量、符号和标志位存放在 lv_tag 中，不再使用 PyVarObject.ob_size 表达符号和长度。

要注意的点：每个int值是一个对象，其中[-5, 256] 这些对象位于运行时全局 small_ints 单例数组中，不会在创建是单独实例化。
