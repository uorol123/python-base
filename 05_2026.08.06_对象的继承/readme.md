Python 支持多继承

## 问题

多继承则重名的使用谁的呢？
MRO（Method Resolution Order，方法解析顺序）——算出一条确定的查找链，按顺序找第一个匹配的
就是谁在前面就用谁

> **GPT 修正**：“直接父类列表中谁靠前”只适合简单例子。Python 使用 **C3 linearization** 计算 `__mro__`，同时保持局部父类顺序和单调性；复杂菱形继承必须以 `SomeClass.__mro__` 为准，某些不一致的基类顺序会在创建类时直接触发 `TypeError`。
