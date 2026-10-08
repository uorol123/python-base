# def保留关键字

 def func(): return 1   编译成：
    LOAD_CONST    <code object func>     ← 1. 把函数体编译成一个 code 对象
    MAKE_FUNCTION 0                      ← 2. 用它造一个 function 对象
    STORE_NAME    func                   ← 3. 绑定到名字 func

用 types.FunctionType(code, globals) 手工造的函数，和 def 出来的本质完全一样。def = 「编译 + 造 function 实例」的简写，正如 class = 「收集类体 + 调元类」的简写
    
## 横向对比
def func(): ...     →  MAKE_FUNCTION 字节码 → 造一个 function 实例
  class Dog: ...      →  type('Dog', bases, ns)  → type.__call__ → type.__new__
  Dog()               →  Dog()                   → type.__call__ → Dog.__new__

> **GPT 修正**：这两行限定在 `type(Dog) is type` 的默认元类场景。完整的类定义还包含 `__build_class__`、元类选择与 `__prepare__`；如果 `Dog` 使用自定义元类，类定义和 `Dog()` 都可能经过该元类覆盖后的逻辑。

# function
function 类型的元类是 type，父类是 object，自己实现了 __call__.
