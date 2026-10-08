# bool
bool 是 int 的子类

也是不可变对象：
/* Py_False and Py_True are the only two bools in existence. */。全局单例：

PyObject *PyBool_FromLong(long ok)
{
    return ok ? Py_True : Py_False;
}

同时，在Cpython中，最终存储是整数值：
False 的整数值是 0
True 的整数值是 1
bool 底层继承 int

判断过程是：
bool(x)
  ↓
PyObject_IsTrue(x) 判断真值
  ↓
得到 0 或 1
  ↓
PyBool_FromLong()
  ↓
返回 Py_False 或 Py_True 单例

## 判断顺序
1. 对象就是 True  → 真
2. 对象就是 False → 假
3. 对象就是 None  → 假
4. 类型实现 __bool__ → 调用 __bool__
5. 类型实现 __len__  → 长度大于0为真，等于0为假
6. 两者都没有        → 默认是真

## 真值协议
类可以自行实现bool，用实例化的对象测试时会调用类的 __bool__ 或  __len__ 来判断。但是这里返回的对象必须要bool类的

## and、or 和not

a and b
- a 为假：直接返回原对象 a
- a 为真：计算并返回原对象 b

a or b
- a 为真：直接返回原对象 a
- a 为假：计算并返回原对象 b

not a
判断a，先把a取bool，直接返回True或False对象

and / or 和 not 根本不是同一类东西。前两个是「控制流」，后一个才是「运算」
从高中开始学习的电路开始就有 与门，或门。

python这里返回的是原对象，只有not才返回True 或False。


### 源码
编译器处理 a and b 的地方在 compile.c:4374 的 compiler_boolop：

  if (e->v.BoolOp.op == And)
      jumpi = POP_JUMP_IF_FALSE;   // and → 假就跳
  else
      jumpi = POP_JUMP_IF_TRUE;    // or  → 真就跳
  for (i = 0; i < n; ++i) {
      VISIT(c, expr, 操作数i);      // 求值
      ADDOP_I(c, loc, COPY, 1);    // 复制一份留栈上
      ADDOP(c, loc, TO_BOOL);      // 只把"副本"转成 bool
      ADDOP_JUMP(c, loc, jumpi, end); // 按真假跳到结尾
      ADDOP(c, loc, POP_TOP);      // 没跳走才弹掉，继续算下一个
  }

  真实反汇编）：

  === a and b ===
    LOAD_NAME  a
    COPY 1                  ← 栈: [a, a]   原件垫底，副本在上
    TO_BOOL                 ← 栈: [a, True/False]   只转换副本！
    POP_JUMP_IF_FALSE → L1  ← 弹掉 bool，为假就跳。栈: [a] ← 原件还活着
    POP_TOP                 ← 为真才弹掉原件，栈: []
    LOAD_NAME  b            ← 现在才求值 b
  L1: RETURN_VALUE          ← 返回栈顶 = 幸存者

二、not：一个真正的「规整化运算」

  compile.c:6233：

  else if (e->v.UnaryOp.op == Not) {
      ADDOP(c, loc, TO_BOOL);
      ADDOP(c, loc, UNARY_NOT);
  }

  === not a ===
    LOAD_NAME  a
    TO_BOOL       ← 第一步：任意对象 → 真单例
    UNARY_NOT     ← 第二步：翻转

  而 UNARY_NOT 的实现（bytecodes.c:329）是整个解释器里最漂亮的指令之一：

  pure inst(UNARY_NOT, (value -- res)) {
      assert(PyBool_Check(value));              // 敢直接断言！
      res = Py_IsFalse(value) ? Py_True : Py_False;   // 纯指针交换
  }

### 短路
非常好理解，or 和 and 不是操作，而是流程，决定操作执不执行， and先判断a，如果a的判断结果为false，直接return b，b如果是语句则不会执行
or 也一样，当a判断为真后，直接return a，a会被执行，但是b不会被执行

### a and b and c 和 a or b or c在做什么
从原理理解就是， a and 【b and c】 先a ，a为false，return 【b and c】，然后执行 b and c。
a or b or c ，先a a为true，return 【b or c】，然后执行b or c 。

## & 和 and
从文件的result4和5打印可以发现：
True & 3 = 1,等价于 1 & 3 ， 1 和 11 ，等于 01 就是 1.
True and 3 = 3
False & 4 = 0
False and 4 = False


& 是按位与，会把两个数转成二进制逐位比较
