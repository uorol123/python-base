str 是字符串，是字符的集合。

## str 内部数组
数组中每个元素的大小必须一致，因为通过索引定位元素必须要位移指定的距离
源码里 s[i] 的真实寻址就是 数据首地址 + i × kind，一步乘法一步加法，O(1)。「定长跨步」是 O(1) 索引的代价

str 内部数组存的是裸码点数值，不是指针，更不指向任何对象:

### str 和 list
| | ['a', 'b', 'c']（list） | 'abc'（str） |
| --- | --- | --- |
| 数组元素 | 指针（8 B） | 码点值（1/2/4 B） |
| 元素是什么 | 堆上离散的 str 对象 | 数字本身（'a' → 97） |
| x[0] 返回 | 已存在的对象（指针解引用） | 现场新建 str 对象（装箱） |
| 'abcdefg' 体积 | ≥ 40 + 7×8 = 96 B | 48 B ✓ |

数字反证：`'a'*1000` 是 1040 B；若是指针数组，光指针就 8000 B（还没算每字符 16 B 对象头）。
Python 没有 char 类型：`s[0]` 是长度 1 的 str，取出时才装箱成对象。
**str 是 CPython 里的「numpy 派」**（裸值连续数组），list 是「对象汤派」（通用、异质、每元素背指针）。
（呼应 10_内存 §1.5：list 装 int 40 B/元素 vs numpy int64 8 B/元素 —— 同一个分叉的两次相遇）

list 也是连续内存：**连续的指针数组**（所以 O(1) 索引），但指针指向的对象散落堆上。
O(1) 的本质是「定长跨步可寻址」，连续定长数组是标准实现（dict 的 indice 数组是另一个变体）。

## PEP 393 灵活字符串表示（3.3+）

### 实测数据（本机 3.13.9 / Win11 64 位）
| 表达式 | getsizeof | 解剖 |
| --- | --- | --- |
| '' | 41 | 40 头 + 1 结尾 \0 |
| 'a' | 42 | +1 |
| 'abcdefg' | 48 | 40 + 7 + 1 |
| '中' | 60 | 56 头 + 2×(1+1) |
| 'ab中cd' | 68 | 56 + 2×(5+1)，a、b 也被拉宽到 2 字节 |
| '𐐷' | 64 | 56 + 4×(1+1) |
| 'héllo' | 62 | 56 + 1×(5+1) |

规律：
1. ASCII 固定成本 40 B，非 ASCII 56 B（两种结构体）
2. **kind 全串统一 —— 木桶效应**：最宽的字符决定全串宽度

### 源码依据
两种结构体 `Include/cpython/unicodeobject.h:99-161`：

```c
typedef struct {
    PyObject_HEAD              // 16 B（10_内存 已学）
    Py_ssize_t length;         // 8 B  码点个数
    Py_hash_t hash;            // 8 B  -1 = 还没算过（惰性缓存）
    struct {
        unsigned int interned:2;              // 驻留状态，4 种
        unsigned int kind:3;                  // 1/2/4 ← 每字符几字节
        unsigned int compact:1;
        unsigned int ascii:1;
        unsigned int statically_allocated:1;
        unsigned int :24;                     // 对齐填充
    } state;                  // 4 B
} PyASCIIObject;              // = 40 B

typedef struct {
    PyASCIIObject _base;
    Py_ssize_t utf8_length;   // 8 B
    char *utf8;               // 8 B  UTF-8 缓存，惰性填充
} PyCompactUnicodeObject;     // = 56 B
```

- kind 四档选择 `Objects/unicodeobject.c:1361-1383`（`PyUnicode_New`）：
  maxchar <128 → 1B + ascii=1（用小结构体 PyASCIIObject）；<256 → 1B（latin-1）；<65536 → 2B；else → 4B
- compact 一次分配 `:1398`：`PyObject_Malloc(struct_size + (size+1)*char_size)`，
  数据紧跟结构体 —— 与 3.13 inline values 同思想：省一次分配 + 缓存友好
- hash 惰性缓存：首次 `hash(s)` 后存进 hash 字段，避免 dict 键反复重算
- `''` 全局单例（`unicodeobject.c:1347` `unicode_get_empty()`），3.13 里 immortal
- str 覆写了 `__sizeof__`（`:13720`）：三种结构分别算，**utf8 缓存也计入**（`:13742`）

### 历史
- ≤3.2：整个解释器统一 `Py_UNICODE`（UCS2/UCS4 **编译期二选一**）：UCS4 构建浪费 3/4，UCS2 构建放不下 emoji
- 3.3 PEP 393：每个字符串**自选最窄宽度**

### 工程视角
- 海量短文本（日志/token/URL）：纯 ASCII 41 B 起；混入一个非 ASCII 字符 → 56 B 起 + 每字符翻倍
- numpy `'U'` dtype 固定 4 字节/字符（UCS4），不做自适应 —— 刻意选「统一」换 SIMD 简单；object dtype 回到指针+独立对象
- 一颗老鼠屎坏一锅粥：`'a'*1000`（1040 B）混入一个 `𐐷` → 跳 4 字节档 ≈ 4056 B

### utf8 缓存彩蛋（实测矛盾）
实测不填缓存：`.encode()`、`os.fsencode`、写 utf-8 文件、`json.dumps`、`%` 格式化、抛异常。
实测填缓存：**sqlite3.execute**（C 扩展）：

```python
import sys, sqlite3
sql = "SELECT 'héllo'"           # 14 字符，latin-1
print(sys.getsizeof(sql))         # 71
con = sqlite3.connect(':memory:')
con.execute(sql).fetchall()
print(sys.getsizeof(sql))         # 87 ← +16
```

+16 的账：é 的 UTF-8 是 2 字节 → 14 字符编码成 15 B + 结尾 \0 = 16 ✓
分叉点：**C 扩展要 `const char*`（指向缓存，可复用）**；`.encode()` 要独立 bytes 对象（不动原串）。
缓存的意义 = 下一次免重算：反复把同一 SQL/路径传给 C 层时只编码一次。

## 误区修正记录（错误 → 证据 → 修正）
1. ~~以为数组存的是指针，指向字符对象~~ → `'a'*1000`=1040 B 实测推翻（指针数组至少 8000 B）→
   真相：**裸码点数组，字符不是对象**，`s[0]` 取出时现场装箱
2. ~~以为 '' 是所有 str 的基石，所有 str 来自它~~ → str 不可变，无「生长」；每个 str 由
   `PyUnicode_New` 独立分配 → '' 单例的真正理由三条件：**不可变 + 全等 + 高频** → 共享只赚不赔（享元）。
   小整数缓存同一逻辑。悬案结案：`Include/internal/pycore_long.h:67` 左闭右开 `[-5, 257)` 即 `[-5, 256]` 闭区间。

## 待学
- [ ] interning 驻留：`state.interned` 2 bit 的四种状态、标识符自动驻留、`is` 判断的前提
- [ ] 拼接性能：`+=` 的 O(n²) 陷阱与 CPython 的偷偷优化、`"".join()` 惯用法
- [ ] f-string 为什么最快（PEP 701）
- [ ] encode/decode 与 UnicodeDecodeError 排查
