"""
三种属性校验方式的完整对比
从 property → 数据描述符(Typed) → TypedModel，逐层消除重复代码

每一节都可以独立运行，建议从上往下逐段看，对比每一层减少了什么重复
"""

from dataclasses import dataclass


# ══════════════════════════════════════════════════════════════════
# 方式一：property —— 每个属性手写 getter + setter
# ══════════════════════════════════════════════════════════════════
#
# 原理：
#   @property 把一个方法变成数据描述符，挂到类属性上
#   @xxx.setter 给这个描述符加上 __set__
#   property 本身就是 C 实现的数据描述符（参见 07_01/readme.md 第五节）
#
# 特点：
#   ✅ 直观，适合 1-2 个属性
#   ❌ 每个属性要写 6-8 行，逻辑高度重复
#   ❌ 每个属性需要一个 _name 私有变量做实际存储

class PersonProperty:
    """用 property 校验：每个属性一套 getter + setter"""

    def __init__(self):
        # 每个属性都需要一个 _xxx 私有变量做实际存储
        self._name = ''
        self._age = 0
        self._email = ''

    # ── name 属性 ──
    @property
    def name(self):           # ← 这就是描述符的 __get__
        return self._name

    @name.setter
    def name(self, value):    # ← 这就是描述符的 __set__
        if not isinstance(value, str):
            raise TypeError(f'name 需要 str，收到 {type(value).__name__}')
        self._name = value

    # ── age 属性 ──（和上面几乎一模一样，只是类型不同）
    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value):
        if not isinstance(value, int):
            raise TypeError(f'age 需要 int，收到 {type(value).__name__}')
        self._age = value

    # ── email 属性 ──（又是一模一样的模式）
    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not isinstance(value, str):
            raise TypeError(f'email 需要 str，收到 {type(value).__name__}')
        self._email = value

    # 想加第 4、5、6 个属性？继续复制粘贴上面 8 行……


# ══════════════════════════════════════════════════════════════════
# 方式二：数据描述符 Typed —— 写一次描述符类，每个属性只需一行
# ══════════════════════════════════════════════════════════════════
#
# 原理：
#   Typed 是一个数据描述符（有 __get__ + __set__）
#   它"包裹"住字段，拦截所有读写
#   值存在 实例自己的 __dict__ 里（不是存在 _xxx 私有变量里）
#
# 关键改进：
#   把方式一里重复的"类型校验 + 存取"逻辑提取到一个类里
#   用的时候只需要声明：name = Typed(str)
#
# 对比 property：
#   property：每个属性 8 行代码
#   Typed：    描述符类写一次，之后每个属性只需 1 行

class Typed:
    """可复用的类型校验描述符"""

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __set_name__(self, owner, name):
        """类创建时 Python 自动调用，告知属性名"""
        # 比如 Person.name = Typed(str) 创建时，
        # Python 会调 Typed.__set_name__(Person, 'name')
        # 这样描述符就知道自己叫 'name' 了
        self.name = name

    def __get__(self, obj, owner):
        # 读 obj.name 时调用
        # obj 可能是 None（类访问 Person.name 时），此时返回描述符自身
        if obj is None:
            return self
        # 从实例自己的 __dict__ 里取值
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        # 写 obj.name = value 时调用
        # 在这里做校验
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f'{self.name} 需要 {self.expected_type.__name__}，'
                f'收到 {type(value).__name__}'
            )
        # 校验通过，存进实例自己的 __dict__
        obj.__dict__[self.name] = value


class PersonTyped:
    """用 Typed 描述符校验：每个属性只需一行"""

    name  = Typed(str)    # ← 就这一行，等同于方式一的 8 行
    age   = Typed(int)    # ← 同样的描述符类，不同的类型参数
    email = Typed(str)    # ← 加第 10 个属性？再写一行就行


# ══════════════════════════════════════════════════════════════════
# 方式三：TypedModel —— 连"每属性一行"都不用写，自动从注解生成描述符
# ══════════════════════════════════════════════════════════════════
#
# 原理：
#   1. 你只写注解：name: str, age: int（跟 dataclass 一样的写法）
#   2. TypedModel 的 __init_subclass__ 在类创建时自动读 __annotations__
#   3. 对每个注解的字段，自动创建一个 Typed 描述符并挂上去
#
# 关键改进：
#   方式二里你要手写 name = Typed(str)
#   方式三里你只需写 name: str，TypedModel 自动帮你做 name = Typed(str)
#
# 这就是 pydantic BaseModel 的核心思路（pydantic 做得更完整、性能更好）

class TypedModel:
    """基类：子类只需写注解，自动获得类型校验"""

    def __init_subclass__(cls, **kwargs):
        """
        子类创建时自动调用（比元类更轻量，效果类似）
        这里的 cls 就是正在创建的子类（比如 PersonModel）
        """
        super().__init_subclass__(**kwargs)
        # 读子类的注解，比如 {'name': str, 'age': int, 'email': str}
        annotations = getattr(cls, '__annotations__', {})
        for field_name, field_type in annotations.items():
            # 自动创建描述符，挂到类上
            # 等同于手写：name = Typed(str)
            descriptor = Typed(field_type)
            # ⚠️ 注意：用 setattr 挂描述符时，Python 不会自动调 __set_name__
            #   __set_name__ 只在 class 体里直接赋值时才自动触发（由 type.__new__ 调）
            #   这里是在 __init_subclass__ 里用 setattr（类已创建完毕），所以要手动设 name
            descriptor.name = field_name
            setattr(cls, field_name, descriptor)


class PersonModel(TypedModel):
    """只需写注解，自动获得类型校验"""

    name:  str           # ← 不再需要 = Typed(str)，__init_subclass__ 自动处理
    age:   int
    email: str

    def __init__(self, name, age, email):
        # __init_subclass__ 已经把 name/age/email 变成了描述符
        # 这里的赋值会触发描述符的 __set__，自动校验
        self.name = name
        self.age = age
        self.email = email


# ══════════════════════════════════════════════════════════════════
# 运行验证：三种方式效果完全一样
# ══════════════════════════════════════════════════════════════════

if __name__ == '__main__':

    def test_property():
        print("方式一 property")
        p = PersonProperty()
        p.name = '张三'
        p.age = 25
        p.email = 'zhangsan@test.com'
        print(f"  name={p.name!r}, age={p.age}, email={p.email!r}")
        try:
            p.age = '二十五'
        except TypeError as e:
            print(f"  校验拦截: {e}")

    def test_typed():
        print("\n方式二 Typed 描述符")
        p = PersonTyped()
        p.name = '李四'
        p.age = 30
        p.email = 'lisi@test.com'
        print(f"  name={p.name!r}, age={p.age}, email={p.email!r}")
        try:
            p.age = '三十'
        except TypeError as e:
            print(f"  校验拦截: {e}")

    def test_typed_model():
        print("\n方式三 TypedModel")
        p = PersonModel('王五', 35, 'wangwu@test.com')
        print(f"  name={p.name!r}, age={p.age}, email={p.email!r}")
        try:
            p.age = '三十五'
        except TypeError as e:
            print(f"  校验拦截: {e}")

    test_property()
    test_typed()
    test_typed_model()

    # ── 对比代码量 ──
    print("\n" + "=" * 60)
    print("代码量对比（3 个属性）")
    print("=" * 60)
    print("""
  方式一 property:
    每个属性：@property + getter + @setter + setter = 8 行
    3 个属性 = 24 行 + 3 个 _xxx 存储变量

  方式二 Typed:
    描述符类：写一次 = 15 行（可复用）
    每个属性：name = Typed(str) = 1 行
    3 个属性 = 15 + 3 = 18 行

  方式三 TypedModel:
    基类 + 描述符：写一次 = 20 行（可复用）
    每个属性：name: str = 1 行（就是普通注解）
    3 个属性 = 20 + 3 = 23 行
    100 个属性 = 20 + 100 = 120 行（property 要 800 行）

  → 属性越多，高阶方式的优势越大
""")

    # ── 验证三种方式底层都是数据描述符 ──
    print("=" * 60)
    print("三种方式的字段都是数据描述符")
    print("=" * 60)

    # property
    print(f"\nPersonProperty.age 有 __set__: {hasattr(type(PersonProperty.age), '__set__')}")
    print(f"  类型: {type(PersonProperty.age).__name__}")        # property

    # Typed
    print(f"\nPersonTyped.age 有 __set__: {hasattr(PersonTyped.age, '__set__')}")
    print(f"  类型: {type(PersonTyped.age).__name__}")           # Typed

    # TypedModel
    print(f"\nPersonModel.age 有 __set__: {hasattr(PersonModel.age, '__set__')}")
    print(f"  类型: {type(PersonModel.age).__name__}")           # Typed
    print("  （__init_subclass__ 自动创建了 Typed 描述符）")
