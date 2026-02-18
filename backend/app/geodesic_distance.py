import heapq
import numpy as np
from typing import Any

class PQueue:
    def __init__(self):
        self.q = []
        self.d: dict[Any, float] = {}

    def push(self, p: float, v: Any):
        heapq.heappush(self.q, (p, v))
        self.d[v] = p

    def pop(self) -> tuple[float, Any]:
        while not self.empty():
            (p, v) = heapq.heappop(self.q)
            if v in self.d and self.d[v] == p:
                self.d.pop(v)
                return (p, v)
        raise IndexError("pop from empty queue")

    def empty(self) -> bool:
        return len(self.d) <= 0

def propagation(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    q = PQueue()
    D = np.full_like(img, 1e10, dtype=np.float64)
    seeds = np.argwhere(mask > 0)
    for seed in seeds:
        D[tuple(seed)] = 0
        q.push(0, tuple(seed))
    while not q.empty():
        p, (l, c) = q.pop()
        for dl in range(-1, 2):
            for dc in range(-1, 2):
                if dl == 0 and dc == 0:
                    continue
                if l + dl < 0 or l + dl >= img.shape[0] or c + dc < 0 or c + dc >= img.shape[1]:
                    continue
                d_new = float(D[l, c] + abs(float(img[l, c]) - float(img[l + dl, c + dc])))
                if d_new < D[l + dl, c + dc]:
                    D[l + dl, c + dc] = d_new
                    q.push(d_new, (l + dl, c + dc))
    return D