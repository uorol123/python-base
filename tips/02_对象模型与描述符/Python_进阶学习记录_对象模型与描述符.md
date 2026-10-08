# Python 进阶学习记录：对象模型与描述符

> 主题：对象命名空间、属性查找与描述符协议  
> 当前阶段：已建立核心心智模型；下一步进入 `__getattribute__` 的实现层理解。  
> 记录原则：这里记录的是已经推导清楚的关联，不把它写成脱离上下文的“定义集合”。后续学习可直接在文末追加。

---

## 1. 这次学习串起来的主线

此前已经接触过 Python 的一些底层概念，但它们像彼此孤立的术语：类属性、实例属性、`__dict__`、方法、描述符、继承。现在可以将它们统一到一个问题：

> 当写下 `a.x` 时，Python 到底从哪里得到 `x`？

这个问题的答案并不是“`a` 里面一定存有 `x`”，而是 Python 的属性访问协议会根据规则，在实例、类及其继承链中查找；描述符还会在查找过程中接管读取或写入。

---

## 2. 对象命名空间：`__dict__` 是“自己存了什么”

```python
class A:
    x = 10

a = A()
b = A()
```

此时可将相关命名空间理解为：

```text
A.__dict__
└── "x" → 10

a.__dict__
└── {}

b.__dict__
└── {}
```

因此：

```python
"x" in a.__dict__  # False
a.x                 # 10
```

两句并不矛盾。`a` 没有**自己存储** `x`，但通过属性访问能够从 `A` 中解析到 `x`。

### 2.1 类属性与实例属性

```python
a.y = 20
```

执行后：

```text
A.__dict__
└── "x" → 10

a.__dict__
└── "y" → 20

b.__dict__
└── {}
```

`y` 是 `a` 的实例属性，只影响 `a`；它不会自动出现在 `b` 中。这一现象的根本原因是不同实例拥有独立的实例命名空间，不是“实例之间继承关系不同”。

---

## 3. 实例化不是继承

```python
class A:
    pass

a = A()
```

应准确区分两条关系：

```text
object
   ↑  （继承）
   │
   A
   ↑  （实例化）
   │
   a
```

```python
issubclass(A, object)  # True：类 A 继承 object
type(a) is A           # True：a 的类型是 A
isinstance(a, A)       # True：a 是 A 的实例
```

所以不能说“`a` 继承了 `object`”。更准确的表述是：

> `A` 继承 `object`；`a` 是 `A` 的实例。

实例化也不会把 `A.__dict__` 里的属性和方法复制一份到 `a.__dict__`。实例可以访问类成员，靠的是属性查找协议。

---

## 4. `a.__dict__["x"]` 与 `a.x` 是两件事

```python
class A:
    x = 10

a = A()
```

```python
a.__dict__["x"]  # KeyError
a.x                # 10
```

前者只是一次普通的字典索引：只检查实例自身的存储空间。后者触发 Python 的属性访问协议，等价方向可粗略理解为：

```python
object.__getattribute__(a, "x")
```

它会结合：

- 实例的 `__dict__`；
- `type(a)`，即类 `A`；
- `A` 的 MRO（方法解析顺序）；
- 类成员是否为描述符。

因此要始终分清：

> “对象自己存储了 `x`”与“通过对象可以访问到 `x`”不是同一个命题。

---

## 5. 属性读取的优先级

针对普通实例 `a` 执行 `a.x`，并以默认的 `object.__getattribute__` 行为为前提，可以先使用下面这张实用优先级表：

| 优先级 | 命中对象 | 说明 |
|---:|---|---|
| 1 | data descriptor（数据描述符） | 类侧对象定义了 `__set__` 或 `__delete__`，读取时优先于实例字典 |
| 2 | `a.__dict__` | 实例自己保存的属性 |
| 3 | non-data descriptor（非数据描述符） | 通常只定义 `__get__`；函数属于这一类 |
| 4 | 普通类属性 | 类或其 MRO 中找到的普通值 |
| 5 | `__getattr__` | 前面正常查找都失败后才调用的兜底 |

类侧的查找不是只看 `A.__dict__`，而是会沿：

```python
type(a).__mro__
```

向上搜索。

### 5.1 `__getattribute__` 与 `__getattr__` 不要混淆

- `__getattribute__`：几乎所有 `a.x` 都先经过它；默认实现承担主要属性查找逻辑。
- `__getattr__`：正常查找失败后才作为兜底调用。

所以把常规访问理解成“先走 `__getattr__`”是不准确的。关键链路应是：

```text
a.x
↓
__getattribute__
↓
按描述符 / 实例字典 / 类与 MRO 的规则查找
↓
仍未找到时，才可能调用 __getattr__
```

---

## 6. 描述符：类属性可以决定“如何被访问”

描述符不是某个固定的类名，而是一个对象：当它作为另一个类的类属性时，如果实现了特定方法，就参与描述符协议。

```python
class D:
    def __get__(self, instance, owner):
        return "读取结果"

class A:
    x = D()
```

这里真正放在类属性位置、参与协议的是：

```python
A.__dict__["x"]  # 一个 D 的实例
```

### 6.1 data descriptor 与 non-data descriptor

```python
class NonData:
    def __get__(self, instance, owner):
        ...

class Data:
    def __get__(self, instance, owner):
        ...

    def __set__(self, instance, value):
        ...
```

- **non-data descriptor**：通常只定义 `__get__`，可被同名实例属性遮蔽。
- **data descriptor**：定义 `__set__` 或 `__delete__`（常见情况下也定义 `__get__`），读取优先级高于实例 `__dict__`，不能被同名实例属性遮蔽。

`property` 是理解数据描述符的典型例子：

```python
class A:
    @property
    def x(self):
        return 100

a = A()
a.__dict__["x"] = 200

print(a.x)  # 100
```

`a.__dict__["x"]` 中的 `200` 的确存在，但 `a.x` 优先命中 `property` 这个数据描述符，因此返回 `100`。

> 术语纠正：标准说法是“数据描述符（data descriptor）”，不是“数据修饰符”。描述符（descriptor）与装饰器（decorator）是两套不同机制。

---

## 7. 函数为何能通过实例调用：绑定方法

```python
class A:
    def hello(self):
        print("hello", self)

a = A()
```

此时：

```python
a.__dict__              # 通常是 {}
A.__dict__["hello"]    # 函数对象
```

`hello` 没有复制到实例中。执行 `a.hello` 时，Python 在类及 MRO 中找到函数对象；普通 Python 函数实现了 `__get__`，因此是 non-data descriptor。它会生成绑定了 `a` 的 bound method。

```text
a.hello
↓
在 A 的 MRO 中找到 function 对象 hello
↓
function.__get__(a, A)
↓
得到绑定方法（bound method）
↓
a.hello() 的效果近似于 A.hello(a)
```

这解释了 `self` 为什么会自动传入，也解释了为什么方法不需要存放在每个实例的 `__dict__` 中。

---

## 8. Attribute shadowing（同名遮蔽）

“遮蔽”不是单一规则，而要看类侧对象的类型。

```python
class A:
    x = 10

a = A()
a.x = 20
```

现在 `a.x` 为 `20`：实例属性遮蔽了普通类属性，`A.x` 仍为 `10`。

对 non-data descriptor 也是类似的：同名实例属性优先。

但对 data descriptor 不成立：

```python
class A:
    @property
    def x(self):
        return 100

a = A()
a.__dict__["x"] = 200
a.x  # 仍为 100
```

一句话总结：

> 实例属性能遮蔽普通类属性和 non-data descriptor；不能遮蔽 data descriptor。

---

## 9. 可变类属性：共享的来源与风险

```python
class A:
    tags = []

a = A()
b = A()
a.tags.append("python")

print(b.tags)  # ["python"]
```

原因不是 `a` 把值“同步”给了 `b`，而是它们都没有自己的 `tags`，所以都通过属性查找访问到了同一个 `A.tags` 列表对象。

```text
A.__dict__["tags"] ──→ 同一个列表对象
                         ↑          ↑
                      a.tags      b.tags
```

常见安全写法是将每个实例独有的可变状态在 `__init__` 中创建：

```python
class A:
    def __init__(self):
        self.tags = []
```

这会让每次实例化都创建一个新列表，并将其放入各自的 `__dict__`。

---

## 10. 已纠正的理解

| 曾经的理解 | 现在的准确说法 |
|---|---|
| `a` 是“继承 `object`、type 为 `A` 的对象” | `A` 继承 `object`；`a` 是 `A` 的实例，且 `type(a) is A` |
| `A` 有 `x`，所以 `a` 也有自己的 `x` | `a.__dict__` 未必有 `x`；`a.x` 可以经由类和 MRO 查找到 `A.x` |
| 实例能调用类方法，是方法被复制进实例 | 函数在类字典中，是 non-data descriptor；访问时生成绑定方法 |
| 常规属性查找主要靠 `__getattr__` | 主流程是 `__getattribute__`；`__getattr__` 是查找失败后的兜底 |
| 不同实例互不影响是继承的核心机制 | 根本原因是实例拥有各自独立的实例命名空间；继承是类之间的关系 |
| “数据修饰符” | 标准术语是“数据描述符（data descriptor）” |

---

## 11. Mental model：一次 `a.x` 的简洁流程图

```text
写下 a.x
   │
   ▼
object.__getattribute__(a, "x")
   │
   ├─ 在 type(a) 的 MRO 中找到同名类属性吗？
   │      │
   │      └─ 是 data descriptor？──是──→ 调用其 __get__，结束
   │
   ├─ a.__dict__ 中有 "x" 吗？──是──→ 返回实例属性，结束
   │
   ├─ 类 / MRO 中找到的对象是 non-data descriptor？──是──→ 调用其 __get__，结束
   │
   ├─ 类 / MRO 中有普通属性？──是──→ 返回类属性，结束
   │
   └─ 正常查找失败
          │
          └─ 若定义了 __getattr__，调用它；否则抛 AttributeError
```

阅读这个模型时，始终保留两个视角：

```text
存储视角：值在哪个 __dict__（或描述符对象）中？
访问视角：写 a.x 时，属性协议按什么优先级解析？
```

---

## 12. 当前学习状态与下一步

### 当前已掌握

已经能从“对象存储”和“属性访问”两个角度解释：

- 为什么类属性没有被复制进实例，实例仍可访问；
- 为什么 `property` 能压过实例字典中的同名值；
- 为什么函数能自动绑定 `self`；
- 为什么同名实例属性有时能遮蔽、有时不能遮蔽类侧定义；
- 为什么可变类属性会在多个实例间共享。

这不是只记住了定义，而是已经建立了描述符与对象模型之间的关联。仍需补齐的主要是实现层的边界：自定义 `__getattribute__`、`super()`、特殊方法查找，以及更完整的 descriptor 写入路径。

### 下一步建议：手写简化版属性查找算法

下一阶段不必继续重复背诵描述符定义，而应将本页的流程图写成一个近似模拟器。目标不是替代 CPython，而是把规则“跑一遍”：

```python
def my_getattribute(obj, name):
    """教学用：模拟 a.x 的主要读取优先级。"""
    cls = type(obj)

    # 1. 在 cls.__mro__ 中寻找 name；若它是 data descriptor，优先返回。
    # 2. 再检查 obj.__dict__。
    # 3. 再处理 non-data descriptor 或普通类属性。
    # 4. 未找到时抛出 AttributeError。
    ...
```

练习时建议准备四类对象：普通类属性、实例属性、只实现 `__get__` 的描述符、实现 `__get__` + `__set__` 的描述符。对同一个属性名分别放入实例和类侧，逐步预测并验证结果。

后续学习可追加：

- `__setattr__` 与 data descriptor 的写入优先级；
- `__delete__`、`property.setter`；
- 自定义 `__getattribute__` 时为何需要避免递归；
- `super()` 与 MRO；
- 特殊方法（如 `__len__`）的查找为何与普通 `a.x` 不完全相同。

---

## 13. 追加记录区

> 后续每次学习可在这里追加：日期、问题、最小示例、自己能解释清楚的结论、仍不确定的边界。

