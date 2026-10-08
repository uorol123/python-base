"""竞态 demo：A1 教科书 demo（3.13 已测不出错）+ A2 真实形状（100% 复现）

对应 tips/01_多线程实战 文档的 Part A。
运行: python race_demo.py
"""
import threading
import time

# ============ A1: 教科书 demo —— 在 3.13 上已经测不出错 ============
import sys
sys.setswitchinterval(1e-6)   # 即使强制频繁让出 GIL

counter = 0

def work():
    global counter
    for _ in range(100_000):
        counter += 1

ts = [threading.Thread(target=work) for _ in range(4)]
for t in ts:
    t.start()
for t in ts:
    t.join()
print(f"A1 教科书竞态: {counter} / 400000  (3.13 实测: 测不出丢失!")
print("   教训: 「我测了没错」不等于线程安全\n")

# ============ A2: 真实形状 —— cache-aside 惰性初始化 ============
cache = {}
init_calls = 0
init_lock = threading.Lock()


def load_from_db(key):
    """模拟一次昂贵的数据库查询"""
    time.sleep(0.01)
    return f"value-{key}"


def get_bad(key):
    global init_calls
    if key not in cache:                  # 检查
        init_calls += 1
        cache[key] = load_from_db(key)    # 动作(慢) —— 窗口大开
    return cache[key]


def get_good(key):
    global init_calls
    with init_lock:                       # 检查+动作 整体原子
        if key not in cache:
            init_calls += 1
            cache[key] = load_from_db(key)
    return cache[key]


def trial(fn, nthreads=8, keys_per_thread=5):
    global init_calls
    cache.clear()
    init_calls = 0

    def work(tid):
        for k in range(keys_per_thread):
            fn(k)

    ts = [threading.Thread(target=work, args=(t,)) for t in range(nthreads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return init_calls


expected = 5  # 只有 5 个不同的 key
print(f"A2 无锁:   初始化 {trial(get_bad)} 次 (期望 {expected}, 大量重复查询)")
print(f"A2 加锁:   初始化 {trial(get_good)} 次 (期望 {expected}) ✓")
