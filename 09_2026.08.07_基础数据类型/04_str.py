s = "asfasgae"
print(s[3])


import sys
for i in ['','a','abcdefg','中','ab中cd','𐐷','héllo']:
    print(sys.getsizeof(i))
sys.getsizeof('')         # 41
sys.getsizeof('a')        # 42
sys.getsizeof('abcdefg')  # 48
sys.getsizeof('中')        # 60
sys.getsizeof('ab中cd')    # 68   ← 注意！
sys.getsizeof('𐐷')        # 64
sys.getsizeof('héllo')    # 62

import numpy as np
a = np.array(['ab', 'cd'])        # dtype '<U2'
# numpy 的 U 类型固定 4 字节/字符（UCS4），不做 PEP 393 那种自适应
# —— 刻意选了「简单统一」而非「按需变窄」，换取 SIMD 友好
b = np.array(['ab', 'cd'], dtype=object)  # 回到指针 + 独立 str 对象
