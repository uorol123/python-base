# ============================================================
#  第 1 课·延伸：Python int 运算为什么慢？numpy 是怎么绕过去的？
# ============================================================
#
# 前面我们看到了：Python 每次做 n += 1，都要 malloc 一个新的 PyLongObject，
# 填值、更新引用计数。500 万次累加耗时 0.5 秒。
#
# 本课回答：numpy 为什么能快几十倍？它底层怎么"绕开"Python 的对象模型？
#
# 核心一句话：numpy 把一整组数字塞进一块连续的 C 数组里，
# 每个数字就是裸的 8 字节（int64），没有对象头、没有指针、没有引用计数。
# 运算直接在 C 层面批量进行，不经过 Python 的"万物皆对象"那一层。
# ============================================================

import sys
import time
import ctypes


# ---------- 1. Python list 的内存布局：指针 + 散落的对象 ----------
#
# 回顾上一节学过的 PyListObject：
#     list 自身 → ob_item（一个 PyObject** 指针数组）
#     ob_item[i] → 指向一个独立的 PyLongObject（28 字节起步）
#
# 所以一个 list of int 的内存长这样（每个数字是独立对象，散落在堆上）：
#
#     list 对象
#     ┌──────────────┐
#     │ ob_item ───────┐
#     │ ob_size = 3   │ │
#     │ allocated = 3 │ │
#     └──────────────┘ │
#                      ▼
#     ob_item 数组（连续的指针，每个 8 字节）
#     ┌────────┬────────┬────────┐
#     │ ptr──┐ │ ptr──┐ │ ptr──┐ │
#     └──────┼─┴──────┼─┴──────┼─┘
#            │        │        │        这些箭头跳到堆上各处
#            ▼        ▼        ▼
#         ┌─────┐  ┌─────┐  ┌─────┐
#         │int 5│  │int 6│  │int 7│   每个都是完整的 PyLongObject（≥28 字节）
#         │28B  │  │28B  │  │28B  │   散落在堆的不同位置
#         └─────┘  └─────┘  └─────┘

py_list = [5, 6, 7]
print('=== 1. Python list 的内存开销 ===')
print(f'list 本身（PyListObject）: {sys.getsizeof(py_list)} 字节')
print(f'  → 这里包含了 ob_item 数组（3 个指针 × 8 字节 = 24 字节）+ 对象头')
print()
print('但每个元素还是独立的 PyLongObject：')
for i, x in enumerate(py_list):
    print(f'  list[{i}] = {x}, id = {id(x)}, sizeof = {sys.getsizeof(x)} 字节')
print()
# 小整数 5/6/7 在缓存里（都是 28 字节），但它们是 3 个独立对象，
# 散落在堆的不同地址。访问 list[0] 要：先读 ob_item[0] 拿指针，再跳过去读对象。


# ---------- 2. numpy ndarray 的内存布局：一块连续的 C 数组 ----------
#
# numpy 的 ndarray 完全不同：
#     ndarray 对象（约 100 字节，固定开销）
#     └── data 指针 → 一块连续的 C 数组
#                       ┌────┬────┬────┐
#                       │ 5  │ 6  │ 7  │   每个元素就是裸的 int64（8 字节）
#                       └────┴────┴────┘   没有对象头、没有指针、紧密排列
#
# 关键区别：
#   - Python list：数据是指针，每个指针跳到独立的 28 字节对象 → 3×(8+28) ≈ 108 字节
#   - numpy array：数据就是值本身，紧密排列 → 3×8 = 24 字节

import numpy as np  # pylint: disable=import-error

np_arr = np.array([5, 6, 7], dtype=np.int64)
print('=== 2. numpy ndarray 的内存布局 ===')
print(f'ndarray 本身（Python 对象）: {sys.getsizeof(np_arr)} 字节   ← 固定开销，跟元素个数无关')
print(f'数据区（裸 C 数组）       : {np_arr.nbytes} 字节   ← 3 个 int64 × 8 字节 = 24 字节')
print(f'dtype = {np_arr.dtype}, itemsize = {np_arr.itemsize} 字节/元素')
print()

# 用 __array_interface__ 看到底层数据的内存地址
print('底层数据的起始地址:', hex(np_arr.__array_interface__["data"][0]))
print()
print('对比：3 个元素的总内存')
print(f'  Python list : {sys.getsizeof(py_list)} (list含指针数组) + 3×{sys.getsizeof(5)} (int对象) = '
      f'{sys.getsizeof(py_list) + 3 * sys.getsizeof(5)} 字节')
# 注意：sys.getsizeof(ndarray) 返回的已经包含了数据缓冲区，不能再加 nbytes！
#   numpy 的 __sizeof__ 文档明确写了：includes memory consumed by the object's data buffer.
#   所以总内存 = sys.getsizeof(arr) 一步到位，不像 list 需要逐个元素另算。
print(f'  numpy array : {sys.getsizeof(np_arr)} 字节   ← 已包含对象头+数据区，不用另加')
print(f'              (对象头≈{sys.getsizeof(np_arr)-np_arr.nbytes}B + 数据区{np_arr.nbytes}B)')
print()


# ---------- 3. 直接读 numpy 的裸字节，证明它就是连续的 C 数组 ----------
#
# 用 ctypes 把 numpy 数据区的字节读出来，你会看到 5/6/7 的 int64 编码紧密排列，
# 中间没有任何"对象头"。

print('=== 3. 直接读 numpy 数据区的原始字节 ===')
addr = np_arr.__array_interface__["data"][0]
raw_bytes = (ctypes.c_uint64 * 3).from_address(addr)
print(f'从地址 {hex(addr)} 读出的 3 个 uint64: {list(raw_bytes)}')
print('  → 就是 5, 6, 7 三个裸数字，紧密排列，没有任何对象头、指针、引用计数')
print()
# 对比：Python list 的元素你没法这样连续读，因为它们散落在堆的各处，
#       每个要先 dereference 指针才能访问。


# ---------- 4. 放大到 500 万元素，看内存差距有多夸张 ----------
#
# 小数组差距不明显，放大到百万级，Python 的"每个数字都是对象"代价就暴露了。

N = 5_000_000
print(f'=== 4. {N:,} 个元素的内存对比 ===')

big_list = list(range(N))
big_arr = np.arange(N, dtype=np.int64)

# Python list 的总内存 = list 本身(指针数组) + 每个元素指向的 int 对象(各 28 字节)
list_mem = sys.getsizeof(big_list) + N * 28
# numpy 的总内存 = sys.getsizeof(ndarray)，已包含数据缓冲区（numpy __sizeof__ 文档明确说明）
arr_mem = sys.getsizeof(big_arr)

print(f'Python list : {list_mem / 1e6:.1f} MB   (≈ {sys.getsizeof(big_list)/1e6:.1f}MB 指针数组 + {N*28/1e6:.1f}MB int对象)')
print(f'numpy array : {arr_mem / 1e6:.1f} MB   (≈ 112B 对象头 + {big_arr.nbytes/1e6:.1f}MB 数据区，sys.getsizeof 一步到位)')
print(f'倍数差距   : {list_mem / arr_mem:.1f}x   ← numpy 省 4 倍以上内存')
print()


# ---------- 5. 运算性能对比：这就是"进阶：整数运算的代价"的终极答案 ----------
#
# 回到第 1 课那个 0.5 秒的 500 万累加。
# Python 每一步：LOAD → long_add → _PyLong_New(malloc) → STORE → 引用计数更新
# numpy 的 sum：一个 C 循环遍历连续数组，CPU 流水线 + SIMD 直接跑，没有对象开销。

print(f'=== 5. 运算性能对比（{N:,} 个元素求和）===')

# Python 原生循环
t0 = time.perf_counter()
s = 0
for x in big_list:
    s += x
t1 = time.perf_counter()
print(f'Python for 循环累加: {t1-t0:.3f} 秒, 结果 = {s}')

# Python 内置 sum（也是 Python 层循环，但优化过一点）
t0 = time.perf_counter()
s = sum(big_list)
t1 = time.perf_counter()
print(f'Python sum():        {t1-t0:.3f} 秒, 结果 = {s}')

# numpy sum（C 层面批量运算）
t0 = time.perf_counter()
s = int(np.sum(big_arr))
t1 = time.perf_counter()
print(f'numpy sum():         {t1-t0:.3f} 秒, 结果 = {s}')

print()
print('→ numpy 快是因为：')
print('  1. 数据连续排列，CPU 缓存命中率高（预取生效）')
print('  2. 没有 malloc/引用计数/对象头开销')
print('  3. 运算在 C 层循环，甚至用 SIMD（一条指令处理多个数据）')
print('  4. 中间结果不创建 Python 对象，只在最后返回时转一次')
print()


# ---------- 6. 用 dis 看 Python 循环的字节码开销 ----------
#
# Python 的 for 循环每次迭代要执行一串字节码（LOAD/ADD/STORE），
# 每条字节码都是一次解释器分发。numpy 的循环是编译好的 C 代码，没有这个开销。

import dis

def loop_sum(lst):
    s = 0
    for x in lst:
        s += x
    return s

print('=== 6. Python 循环的字节码（每次迭代都走这一遍）===')
dis.dis(loop_sum)
print()
print('↑ 每次迭代：FOR_ITER → STORE_NAME(x) → LOAD_NAME(s) → LOAD_NAME(x) → INPLACE_ADD → STORE_NAME(s)')
print('  光是循环体就有 5+ 条字节码，每条都要解释器分发一次。')
print('  numpy 的 np.sum() 整个循环体是 C 编译后的机器码，没有字节码分发开销。')
print()


# ---------- 总结 ----------
print('=== 总结：numpy 绕开了什么 ===')
print('Python 的"万物皆对象"是优雅的设计，但运算时有 3 层税：')
print('  ① 每个数字 ≥28 字节（对象头）           → 内存浪费')
print('  ② 每次运算 malloc 新对象 + 引用计数      → CPU 开销')
print('  ③ 每步循环走字节码分发                    → 解释器开销')
print()
print('numpy 的做法：数据用 C 的连续数组（int64 = 8 字节/个，无对象头），')
print('              运算用 C 循环（无 malloc、无字节码、有 SIMD）。')
print('              这就是为什么 numpy 是 Python 科学计算的基石。')
