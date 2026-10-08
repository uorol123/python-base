"""验证用：BatchShipper 组件 + 竞态 demo，全部跑通后写进 tips"""
import threading, queue, time
from dataclasses import dataclass


@dataclass(slots=True)
class Record:
    level: str
    msg: str


class BatchShipper:
    """多线程安全的后台批量上报器：攒一批再发（按条数或按时间触发）。"""

    def __init__(self, batch_size=100, flush_interval=0.5, maxsize=10_000, sink=None):
        self._q: queue.Queue[Record] = queue.Queue(maxsize=maxsize)  # 有界队列 => 背压
        self._stop = threading.Event()                                # 关闭信号
        self._batch_size = batch_size
        self._interval = flush_interval
        self._sink = sink or (lambda batch: None)   # 真实场景: HTTP POST / 批量写库
        self._drop_count = 0
        self._thread = threading.Thread(
            target=self._run, name="BatchShipper", daemon=True)
        self._thread.start()

    # ---- 生产者侧（任意线程调用都安全）----
    def submit(self, record: Record) -> None:
        try:
            self._q.put(record, timeout=1.0)   # 队列满则阻塞：把压力传回生产者
        except queue.Full:
            self._drop_count += 1              # 或者选择丢弃+计数，二选一，别静默

    # ---- 消费者（唯一的后台线程）----
    def _run(self) -> None:
        batch: list[Record] = []
        last_flush = time.monotonic()
        while not self._stop.is_set():
            try:
                # 带超时的 get：空闲时也能按时间刷新，同时能及时响应关闭
                batch.append(self._q.get(timeout=0.05))
                self._q.task_done()
            except queue.Empty:
                if batch and time.monotonic() - last_flush >= self._interval:
                    self._safe_deliver(batch)
                    batch, last_flush = [], time.monotonic()
                continue
            if len(batch) >= self._batch_size:
                self._safe_deliver(batch)
                batch, last_flush = [], time.monotonic()
        # 收到关闭信号：把队列里剩余的清完再退出（不丢数据）
        while True:
            try:
                batch.append(self._q.get_nowait())
                self._q.task_done()
            except queue.Empty:
                break
        if batch:
            self._safe_deliver(batch)

    def _safe_deliver(self, batch: list[Record]) -> None:
        """线程里的异常不会传播到主线程，必须自己接住，否则线程静默死亡。"""
        try:
            self._sink(batch)
        except Exception:
            pass  # 真实场景: 重试队列 / 计数 + 告警, 绝不让 worker 死掉

    # ---- 关闭（支持 with）----
    def close(self, timeout: float = 5.0) -> bool:
        self._stop.set()
        self._thread.join(timeout)
        return not self._thread.is_alive()     # False = 没能优雅退出

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None                            # 不吞异常，只负责收尾


# ================= 测试 =================
sent: list[list[Record]] = []
lock = threading.Lock()          # sink 也会被 close 时的主线程并发碰到? 不会，但演示用

def sink(batch):
    with lock:
        sent.append(batch)

print("=== T1: 4 个生产者线程共提交 1000 条，batch_size=100 ===")
with BatchShipper(batch_size=100, flush_interval=5.0, sink=sink) as shipper:
    def producer(tid):
        for i in range(250):
            shipper.submit(Record("info", f"t{tid}-{i}"))
    ts = [threading.Thread(target=producer, args=(t,)) for t in range(4)]
    for t in ts: t.start()
    for t in ts: t.join()
    shipper._q.join()            # 等所有条目被处理完
time.sleep(0.1)
total = sum(len(b) for b in sent)
print(f"批次数={len(sent)}, 总条数={total}, 期望 10 批 / 1000 条")

print()
print("=== T2: 时间触发 —— 只有 3 条，到点也发 ===")
sent.clear()
with BatchShipper(batch_size=100, flush_interval=0.3, sink=sink) as s:
    s.submit(Record("info", "a"))
    s.submit(Record("info", "b"))
    s.submit(Record("info", "c"))
    time.sleep(0.6)              # 超过 flush_interval
print(f"关闭前已发批次: {[len(b) for b in sent]} (期望 [3] 或 [3]+[])")

print()
print("=== T3: 优雅关闭不丢数据 —— 提交后立刻关 ===")
sent.clear()
s = BatchShipper(batch_size=10_000, flush_interval=60, sink=sink)
for i in range(57):
    s.submit(Record("info", str(i)))
ok = s.close(timeout=2)
print(f"优雅退出={ok}, 剩余批次大小={[len(b) for b in sent]} (期望 57)")

print()
print("=== T4: 竞态 demo —— GIL 不等于线程安全 ===")
counter = 0
def work():
    global counter
    for _ in range(100_000):
        counter += 1
ts = [threading.Thread(target=work) for _ in range(4)]
for t in ts: t.start()
for t in ts: t.join()
print(f"期望 400000, 实际 {counter} (少了 {400000 - counter})")

counter2 = 0
lock2 = threading.Lock()
def work_safe():
    global counter2
    for _ in range(100_000):
        with lock2:
            counter2 += 1
ts = [threading.Thread(target=work_safe) for _ in range(4)]
for t in ts: t.start()
for t in ts: t.join()
print(f"加锁后: {counter2} (正确)")
