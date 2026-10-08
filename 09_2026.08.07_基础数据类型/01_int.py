# ============================================================
#  第 1 课：int —— 为什么 Python 的整数永远不会溢出？
# ============================================================
# GPT 修正：Python int 是任意精度整数，常规整数运算不会发生固定宽度的回绕溢出，
# 但仍受可用内存、容器/接口的 Py_ssize_t 边界以及转换到 C/NumPy 固定宽度类型时的范围限制。
#
# 前置知识（你已学过）：
#   - 对象三要素 id / type / value
#   - 不可变对象：值不能原地改，"改"其实是新建对象
#   - 02_对象相关 里留的课后思考 Q1：a=100; b=100 时 a is b 为何是 True
#
# 本课要回答 4 个问题：
#   Q1. C 语言的 int 会溢出（32 位最多约 21 亿），Python 的 int 几百位都不溢出，底层怎么做到的？
#   Q2. sys.getsizeof(0)=28, getsizeof(1)=28，0 没有数据为什么也占 28 字节？数字越大占内存越多吗？
#   Q3. 小整数缓存 [-5, 256] 是什么？什么时候建的？为什么是这个范围？
#   Q4. 既然 int 不可变，那 n += 1 到底"改"了什么？
#
# 学习方式：跑一遍 → 看输出 → 不懂的回头问 → 进第 2 课
# ============================================================


# ---------- Q1 + Q2：int 的 C 语言结构 PyLongObject ----------
#
# CPython 源码里（Include/cpython/longintrepr.h），一个 int 对象长这样：
#
#   struct PyLongObject {
#       PyObject_VAR_HEAD     // ← 变长对象头：ob_refcnt, ob_type, ob_size（共 24 字节）
#       digit ob_digit[1];    // ← 柔性数组（flexible array member），uint32_t，每个存 30 位
#   };
#
# GPT 修正（CPython 3.13）：上面是旧版本心智模型。当前源码实际接近：
#   struct _longobject { PyObject_HEAD; _PyLongValue long_value; };
#   _PyLongValue = { uintptr_t lv_tag; digit ob_digit[1]; }
# digit 数量、符号和标志位存放在 lv_tag 中，不再使用 PyVarObject.ob_size 表达符号和长度。
#
# 关键在 ob_digit 这个柔性数组：
#   - 每个 digit 是 32 位无符号整数，但只用其中 30 位存数据（留 2 位给进位/符号处理）
#   - 数字越大，ob_digit 数组就越长 —— 所以 int 理论上没有上限，只受内存限制
#   - 这就是"任意精度整数"(arbitrary-precision integer)
#
# ob_size 字段记录 ob_digit 数组用了几个槽：
#   ob_size = 0          → 数字是 0（ob_digit 里啥也没有）
#   ob_size > 0          → 正数，用 |ob_size| 个 digit
#   ob_size < 0          → 负数，符号放在 ob_size 上，digit 本身只存绝对值
#
# 换算公式：int 的值 = sum( ob_digit[i] * (2^30)^i )  for i in range(abs(ob_size))
#   即一个"以 2^30 为基"的多位计数法，跟十进制原理一样，只是基变成了 2^30。
# GPT 修正：CPython 3.13 中公式本身仍成立，但 digit 数量应从 lv_tag 的高位解码，
# 符号来自 lv_tag 的低位；30-bit digit 取决于构建配置，可用 sys.int_info.bits_per_digit 验证。

import sys

print('=== Q1/Q2. int 的内存大小 ===')
print(f'sys.getsizeof(0)        = {sys.getsizeof(0)}    字节   ← 0 也占 28！见下方解读')
print(f'sys.getsizeof(1)        = {sys.getsizeof(1)}    字节   ← 和 0 一样大，因为柔性数组预留了 1 个槽')
print(f'sys.getsizeof(2**30-1)  = {sys.getsizeof(2**30-1)}    字节   ← 30 位刚好塞进 1 个 digit')
print(f'sys.getsizeof(2**30)    = {sys.getsizeof(2**30)}    字节   ← 进位了！需要第 2 个 digit')
print(f'sys.getsizeof(2**60)    = {sys.getsizeof(2**60)}    字节   ← 需要 3 个 digit')
print(f'sys.getsizeof(10**100)  = {sys.getsizeof(10**100)}    字节   ← 100 位十进制，约 12 个 digit')
print()
# 解读：64 位系统上 PyLongObject 的内存布局：
#     ob_refcnt  (8 字节) ┐
#     ob_type    (8 字节) ├─ PyObject_VAR_HEAD，固定 24 字节
#     ob_size    (8 字节) ┘
#     ob_digit[] (每个 4 字节)
#
# 所以总大小 = 24 + 4 * |ob_size|
#   - 0：ob_size=0，但柔性数组编译时预留了 1 个槽位 → 24 + 4 = 28 字节（这个槽空着没用）
#   - 1 ~ 2^30-1：ob_size=1，用满那 1 个预留槽 → 还是 28 字节
#   - 2^30 起：ob_size=2，柔性数组真正"生长"一格 → 28 + 4 = 32 字节
#
# 这就解释了为什么 0 和 1 一样大：结构体本身就带着 1 个预留的 digit 槽位，
# 小数字刚好填进这个槽，不需要额外扩容。从 2^30 开始才真正"长个儿"。
# GPT 修正（当前 64 位 CPython 3.13）：观察到的 24 字节前缀是
# PyObject_HEAD(16) + lv_tag(8)，再加至少一个 4 字节 digit；分配器始终至少留一个 digit。
# `sys.getsizeof` 报告的是对象自身逻辑大小，不等价于底层 allocator 实际占用的完整块大小。
#
# 对比 C 语言的 int：C 里 int 永远是 4 或 8 字节，所以有上限（INT_MAX ≈ 2.1e9）。
# GPT 修正：C 标准不保证 int 一定是 4 或 8 字节，只规定最小范围及类型间关系；
# 主流平台通常是 32-bit int。应使用 sizeof(int)、CHAR_BIT、INT_MAX 检查具体 ABI。
# Python 用"可变长度数组"换来了"永不溢出"，代价是每个 int 至少 28 字节、且运算要逐位处理。


# ---------- Q3：小整数缓存 [-5, 256] ----------
#
# CPython 启动时（_PyLong_Init），会预先 new 出 -5 到 256 这 262 个 int 对象，
# 放进一个全局数组 small_ints[]。之后所有代码里用到这个范围的整数，
# 都直接返回数组里那个现成对象的指针，绝不重复创建。
#
# 为什么是这个范围？
#   - 负数到 256 是 Python 内部循环、索引、计数最常碰到的数字
#   - 256 恰好是 2^8，字节运算的边界
#   - 262 个对象占的内存（约 7KB）完全可接受，但收益极大
#
# GPT 修正（CPython 3.13）：[-5, 256] 的范围可由 _PY_NSMALLNEGINTS=5、
# _PY_NSMALLPOSINTS=257 直接验证；这些对象位于运行时全局 small_ints 单例数组中。
# “因为循环/索引常用且 256 是字节边界”是合理解释，但不是源码给出的正式设计证明，
# 应标为设计动机推测，而不是已证实事实。
#
# 一个直接推论：
#   a = 100; b = 100   →  a is b 是 True（指向同一个缓存对象）
#   a = 300; b = 300   →  在 REPL 里 a is b 是 False（每次新建对象）

print('=== Q3. 小整数缓存 [-5, 256] ===')
a, b = 100, 100
print(f'100 is 100  → {a is b}     ← 在缓存范围内，两个名字指向同一个对象')
a, b = 256, 256
print(f'256 is 256  → {a is b}     ← 256 在范围内（闭区间）')
a, b = -5, -5
print(f' -5 is -5   → {a is b}     ← -5 也在范围内')
a, b = 257, 257
print(f'257 is 257  → {a is b}     ← 257 超出范围！按理应是 False，但这里 True，见下方"常量折叠"')
print()


# ---------- 坑：常量折叠 —— 为什么 .py 里 257 is 257 居然是 True？ ----------
#
# 上面 257 is 257 打印 True，跟"超出小整数缓存"矛盾！
# 原因是 CPython 编译 .py 时，会把同一个 code block（模块/函数体）内的相同字面量
# 合并到字节码常量池 co_consts 的同一条目 —— 两个名字绑到同一个对象上。
# 这跟"运行时新建"是两回事，是编译期的优化。
#
# 注意：REPL 里每行单独编译成一个 code block，没机会合并，所以 REPL 里 257 is 257 是 False。
#       这个差异只能靠你自己开 REPL 验证（.py 文件里永远演示不出 REPL 的 False）。

print('=== 常量折叠的坑 ===')
a = 257
b = 257                                   # 两条独立赋值语句，但字面量相同
print(f'a=257; b=257          → a is b = {a is b}     ← .py 里 True：编译器把两个 257 合并成同一个常量')

a = 257
b = int("257")                            # 运行时新建对象，绕过编译期优化
print(f'a=257; b=int("257")   → a is b = {a is b}    ← False：这才是"值相等但非同一对象"的可靠演示')
# 教训：要可靠地判断"两个值相等的整数是不是同一对象"，
#       永远用 int(...) 这类运行时构造，不要用裸字面量（你 02_对象相关 那份笔记里也踩过同样的坑）。
# GPT 修正：这能在当前 CPython 中构造出缓存范围外的新对象，但“永远”不属于语言保证。
# 身份复用是实现细节；业务代码只应使用 == 比较整数值，is 仅用于 None 等单例语义。
print()


# ---------- Q4：int 不可变，那 n += 1 到底干了啥？ ----------
#
# n += 1 在字节码层面是：
#   1. LOAD_NAME n            → 把 n 当前指向的对象（比如 10）取出来
#   2. LOAD_CONST 1           → 取常量 1
#   3. BINARY_ADD             → 调用 long_add(10, 1)，**新建**一个值为 11 的 int 对象
#   4. STORE_NAME n           → 把名字 n 重新绑定到这个新对象
# GPT 修正（Python 3.13）：模块级实际字节码使用 BINARY_OP 13 (+=)，而不是 BINARY_ADD。
# 在函数局部还会看到 LOAD_FAST/STORE_FAST，并可能被自适应解释器专门化。
#
# 注意第 3 步：long_add 是 C 函数，它 malloc 一块新内存、构造一个新的 PyLongObject，
# 把 11 填进去。原来的 10 对象一点没动（它还在小整数缓存里躺着）。
# 这就是"不可变"的精确含义：对象自身的 ob_digit 内容永远不变；变的只是名字的指向。
# GPT 修正：`10 + 1` 的数学结果是新值，但 CPython 会把结果规范化为小整数单例 11，
# 因而这里不会为 11 新分配 PyLongObject。不可变只保证原对象不被原地修改，
# 不保证每次运算都产生一个全新身份的对象。
#
# 用 id 验证：

print('=== Q4. n += 1 的真相 ===')
n = 10
print(f'n = 10 时 id(n) = {id(n)}')
n += 1
print(f'n += 1 后 id(n) = {id(n)}   ← id 变了！n 指向了一个全新的对象 11')
print(f'顺带：id(10) = {id(10)}, id(11) = {id(11)}   ← 都是缓存里早就建好的对象')
print(f'所以 n += 1 前后 id(n) 分别等于 id(10) 和 id(11)：纯粹是换了个指向')
print('GPT 修正：这里的 11 来自小整数缓存，不是本次 += 新分配的对象。')
print()


# ---------- 进阶：整数运算的代价 ----------
#
# 因为 int 运算每次都新建对象，所以下面这种"循环累加"在 Python 里其实挺贵的：
#   s = 0
#   for i in range(10**7): s += i
# 每次 += 都：malloc 新 PyLongObject → 填值 → 旧对象引用计数减 1 → 可能 GC
# GPT 修正：累计值超出小整数缓存后，大多数迭代确实会产生新的 PyLongObject，
# 但不应写成每次都直接 malloc；CPython 通过自己的对象内存分配器工作，并存在快速路径。
# int 不是 cyclic GC 跟踪对象，旧整数通常在引用计数归零时释放，不是“可能由循环 GC 回收”。
# 对比 C 的 s += i，只是改一个寄存器里的 4 字节，差着数量级。
#
# 这也是为什么"计算密集任务用 numpy"——numpy 把一整组数字放进一个连续的 C 数组，
# 绕开了 Python 的"每个数字都是独立对象"这一层。

print('=== 进阶：运算代价（感受一下） ===')
import time
t0 = time.perf_counter()
s = 0
for i in range(5_000_000):
    s += i
t1 = time.perf_counter()
print(f'累加 500 万次：s = {s}，耗时 {t1-t0:.3f} 秒')
print('↑ 这 500 万次里，每一次 += 都新建了一个 int 对象。换成 numpy 会快几十倍。')
print('GPT 修正：缓存范围内的结果会复用单例；超出后大多数累加结果才需要新整数对象。')
print()


# ---------- 课后思考 ----------
print('=== 课后思考（下一课或之后揭晓） ===')
print('Q-A: is 的判断依据是 id，那缓存范围外的整数，什么时候会出现"两个值相等但 is False"？')
print('Q-B: sys.int_info 里藏着 CPython 的整数实现细节，跑一下看看，能猜出每个字段什么意思吗？')
print(f'     sys.int_info = {sys.int_info}')
print('Q-C: 0 的 ob_size 是 0（没有 digit），那 -1 的 ob_size 是多少？符号存在哪？')
print('GPT 修正（3.13）：应改问 lv_tag 如何编码 digit 数量与符号；当前实现不再用 ob_size。')
