# ============================================================
#  第 1 课：int —— 为什么 Python 的整数永远不会溢出？
# ============================================================
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
#
# 对比 C 语言的 int：C 里 int 永远是 4 或 8 字节，所以有上限（INT_MAX ≈ 2.1e9）。
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
print()


# ---------- Q4：int 不可变，那 n += 1 到底干了啥？ ----------
#
# n += 1 在字节码层面是：
#   1. LOAD_NAME n            → 把 n 当前指向的对象（比如 10）取出来
#   2. LOAD_CONST 1           → 取常量 1
#   3. BINARY_ADD             → 调用 long_add(10, 1)，**新建**一个值为 11 的 int 对象
#   4. STORE_NAME n           → 把名字 n 重新绑定到这个新对象
#
# 注意第 3 步：long_add 是 C 函数，它 malloc 一块新内存、构造一个新的 PyLongObject，
# 把 11 填进去。原来的 10 对象一点没动（它还在小整数缓存里躺着）。
# 这就是"不可变"的精确含义：对象自身的 ob_digit 内容永远不变；变的只是名字的指向。
#
# 用 id 验证：

print('=== Q4. n += 1 的真相 ===')
n = 10
print(f'n = 10 时 id(n) = {id(n)}')
n += 1
print(f'n += 1 后 id(n) = {id(n)}   ← id 变了！n 指向了一个全新的对象 11')
print(f'顺带：id(10) = {id(10)}, id(11) = {id(11)}   ← 都是缓存里早就建好的对象')
print(f'所以 n += 1 前后 id(n) 分别等于 id(10) 和 id(11)：纯粹是换了个指向')
print()


# ---------- 进阶：整数运算的代价 ----------
#
# 因为 int 运算每次都新建对象，所以下面这种"循环累加"在 Python 里其实挺贵的：
#   s = 0
#   for i in range(10**7): s += i
# 每次 += 都：malloc 新 PyLongObject → 填值 → 旧对象引用计数减 1 → 可能 GC
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
print()


# ---------- 课后思考 ----------
print('=== 课后思考（下一课或之后揭晓） ===')
print('Q-A: is 的判断依据是 id，那缓存范围外的整数，什么时候会出现"两个值相等但 is False"？')
print('Q-B: sys.int_info 里藏着 CPython 的整数实现细节，跑一下看看，能猜出每个字段什么意思吗？')
print(f'     sys.int_info = {sys.int_info}')
print('Q-C: 0 的 ob_size 是 0（没有 digit），那 -1 的 ob_size 是多少？符号存在哪？')
