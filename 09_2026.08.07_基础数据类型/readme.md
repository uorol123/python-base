# 对象
对象3要素 id / type / value

## 不可变对象
不可变对象的定义是：value 在生命周期内不能被原地修改。跟"内存大小是否固定"没有因果关系。
不可变对象的所谓修改是新建对象 + 名字重新绑定：创建一个全新的对象，名字重新绑定到新对象。不是"原对象重新分配内存"——原对象一点没动，还躺在内存里（如果是缓存对象如 10，会一直躺着）
可变/不可变是"类型设计契约"：这个类型的实例，允许不允许被人原地改它的 value。跟内存大小是否固定无关

### 主要常用类型

int（整数）
float（浮点数）
bool（布尔值）
str（字符串）
tuple（元组） —— 注意：元组不可变是指它的“引用”不可变，如果元组内包含列表，该列表的内容是可变的。
> **GPT 修正**：更精确地说，tuple 保存的**元素引用序列不能被原地替换、增加或删除**；它引用的对象仍遵循各自类型的可变性。因此 tuple 包含 list 时，tuple 结构没变，但 list 的内部状态可以变化。另需注意：这种 tuple 通常不可哈希，不能直接作为 `dict` 键。
frozenset（冻结集合）
bytes（字节序列）

## 可变对象
可变对象的定义是：实例创建后，value 可以在生命周期内被原地修改（in-place），修改前后 id() 不变。同样是类型设计契约：这个类型允许别人原地改它的 value。
可变类型的“修改”是原对象内部状态变化，所有指向它的名字（别名）都能看到这个变化——这是可变对象一切坑的根源。

### 主要常用类型
- list（列表）
- dict（字典）
- set（集合）
- bytearray（字节数组）
- 自定义类的实例（默认可变）

  - 标准库里可变/不可变是成对设计的：bytes ↔ bytearray，set ↔ frozenset，tuple ↔ list。而 str故意没有可变版本（io.StringIO 是替代品）
  - 可变对象通常不可哈希（list/dict/set 不能作 dict 键）——因为哈希值由 value 决定，原地改了value，哈希就失效了。但自定义类实例是个“不一致”特例：默认既可变又可哈希（按 id 哈希）


# 目录
    int:
    - 不会像c语言一样溢出
    - 是对象
    - numpy为什么快
    - 小整数缓存 [-5, 256)：为什么 257 is 257 有坑，== 与 is 的选择
    - int("字符串") 的 4300 位限制：二次方复杂度被禁的由来（工程上真实的 CVE）
    - 大数运算的性能特征：什么时候该换 numpy
    float:
    - 精度边界和范围边界
    - 为什么能和int进行运算
    - 为什么0.1 + 0.2 != 0.3
    - 特殊值：inf、nan，为什么 nan != nan，判空用 math.isnan 而不是 ==
    - 为什么 hash(1) == hash(1.0)：数值跨越类型的哈希一致性
    - math.isclose / decimal.Decimal / fractions.Fraction —— 精度问题的标准库答案（你的生态重点方向）
    bool:
    - 真值协议
    - and、or、not
    - 短路运算
    - bool 继承 int
    - True 与 1 的哈希相同，作为字典键会发生重合
    - if x 与 if x is None 的语义区别
    - &、|、^ 与 and、or 的区别
    - any()、all() 的短路行为
    - NumPy/Pandas 多元素对象不能直接进行真值判断，应使用 .any() 或 .all()
        
    str（内容最多的一个）：
    - ⭐ PEP 393 紧凑表示：ASCII/UCS1/UCS2/UCS4 怎么选
    - ⭐ 字符串驻留 interning：sys.intern、标识符自动驻留、is 判断的前提
    - 🔧 拼接性能：+= 的 O(n²) 陷阱与 CPython 的偷偷优化、"".join() 惯用法
    - 🔧 f-string 为什么最快（PEP 701）
    - 📦 encode/decode 与 UnicodeDecodeError 的排查
    
    tuple：
    - ⭐ 为什么比 list 省内存：源码里的定长分配
    - ⭐ 可哈希的数学与工程意义（呼应你已有的 frozenset 笔记）
    - 🔧 打包解包：a, b = b, a 在字节码层发生了什么（ROT）
    - 📦 namedtuple / NamedTuple

    list：
    - ⭐ over-allocation 增长策略：list_resize 的近似 1.125 倍扩容，append 为什么均摊 O(1)
    - 🔧 insert(0,x) 的 O(n) → collections.deque
    - ⭐ sort 的进化：Timsort → powersort（3.11+）
    - 🔧 浅拷贝三种写法与 copy.deepcopy
    - 🔧 遍历时修改的坑
    - 📦 array.array / numpy：为什么连续存储快
    
    dict：
    - ⭐ 紧凑布局+插入有序（3.6+）： indice 数组 + entries 数组
    - ⭐ 开放寻址与 perturb 扰动：哈希冲突怎么解决
    - 📦 defaultdict / Counter / ChainMap / setdefault 与 __missing__
    - 🔧 遍历时增删的坑
    - 🔧 dict vs dataclass 的选型
    
    set：
    - ⭐ 与 dict 共享哈希表技术但无值槽
    - 🔧 去重与集合运算的惯用法
    - ⭐ frozenset 存在的意义（作键、缓存）
    
    bytearray（小项）：
    - 🔧 为什么需要可变字节：IO 缓冲场景
    - 📦 memoryview + struct：零拷贝解析二进制协议
    
    通用主题（学完上面后收尾用）：
    - ⭐ 函数默认参数 def f(x=[]) 的坑：可变默认值与 None 哨兵
    - ⭐ 别名与共享引用：a = b 之后发生了什么
    - 🔧 copy vs deepcopy 的边界
