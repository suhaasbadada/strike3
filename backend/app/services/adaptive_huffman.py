import math

class Node:
    def __init__(self, weight=0, symbol=None, parent=None, order=0):
        self.weight = weight
        self.symbol = symbol
        self.parent = parent
        self.left = None
        self.right = None
        self.order = order

    def is_leaf(self):
        return self.left is None and self.right is None

class AdaptiveHuffman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.MAX_ORDER = 512
        self.root = Node(0, "NYT", None, self.MAX_ORDER)
        self.nyt = self.root

        self.symbol_table = {}
        self.order_table = {self.root.order: self.root}

    # entropy calculation
    def _entropy(self, text: str) -> float:
        if not text:
            return 0.0

        freq = {}
        for c in text:
            freq[c] = freq.get(c, 0) + 1

        entropy = 0.0
        total = len(text)

        for count in freq.values():
            p = count / total
            entropy -= p * math.log2(p)

        return round(entropy, 4)

    # code from node
    def _get_code(self, node):
        bits = []
        while node.parent:
            bits.append(0 if node.parent.left == node else 1)
            node = node.parent
        return bits[::-1]

    # find swap node (FGK basic)
    def _is_ancestor(self, ancestor, node):
        current = node.parent
        while current is not None:
            if current is ancestor:
                return True
            current = current.parent
        return False

    def _find_swap_node(self, node):
        for order in sorted(self.order_table.keys(), reverse=True):
            candidate = self.order_table[order]
            if (
                candidate.weight == node.weight
                and candidate is not node
                and candidate is not node.parent
                and not self._is_ancestor(candidate, node)
                and not self._is_ancestor(node, candidate)
            ):
                return candidate
        return None

    # swap nodes
    def _swap(self, a, b):
        if a.parent is None or b.parent is None:
            return
        if a.parent == b or b.parent == a:
            return

        pa, pb = a.parent, b.parent

        if pa.left == a:
            pa.left = b
        else:
            pa.right = b

        if pb.left == b:
            pb.left = a
        else:
            pb.right = a

        a.parent, b.parent = pb, pa

        self.order_table[a.order], self.order_table[b.order] = b, a
        a.order, b.order = b.order, a.order

    # update tree
    def _update(self, node):
        while node:
            swap_node = self._find_swap_node(node)
            if swap_node and swap_node != node.parent:
                self._swap(node, swap_node)

            node.weight += 1
            node = node.parent

    # add new symbol
    def _add_symbol(self, symbol):
        old = self.nyt

        internal = Node(1, None, None, old.order)
        new_leaf = Node(1, symbol, internal, old.order - 1)
        new_nyt = Node(0, "NYT", internal, old.order - 2)

        internal.left = new_nyt
        internal.right = new_leaf

        if old.parent:
            p = old.parent
            if p.left == old:
                p.left = internal
            else:
                p.right = internal
            internal.parent = p
        else:
            self.root = internal
            internal.parent = None

        self.nyt = new_nyt
        self.symbol_table[symbol] = new_leaf

        self.order_table[internal.order] = internal
        self.order_table[new_leaf.order] = new_leaf
        self.order_table[new_nyt.order] = new_nyt

        self._update(internal.parent)

    # process symbol
    def _process(self, symbol):
        if symbol in self.symbol_table:
            self._update(self.symbol_table[symbol])
        else:
            self._add_symbol(symbol)

    # pack, unpack
    def _pack(self, bits):
        padding = (8 - len(bits) % 8) % 8
        bits += [0] * padding

        out = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for b in bits[i:i+8]:
                byte = (byte << 1) | b
            out.append(byte)

        return bytes(out), len(bits) - padding

    def _unpack(self, data):
        bits = []
        for b in data:
            for i in range(7, -1, -1):
                bits.append((b >> i) & 1)
        return bits

    # encode
    def encode(self, text: str) -> bytes:
        self.reset()

        data = text.encode("utf-8")
        bits = []

        for byte in data:
            if byte in self.symbol_table:
                bits.extend(self._get_code(self.symbol_table[byte]))
            else:
                bits.extend(self._get_code(self.nyt))
                bits.extend([int(b) for b in f"{byte:08b}"])

            self._process(byte)

        packed, bit_len = self._pack(bits)

        return (
            len(data).to_bytes(4, "big")
            + bit_len.to_bytes(4, "big")
            + packed
        )

    # decode
    def decode(self, data: bytes) -> str:
        if len(data) < 8:
            return ""

        self.reset()

        orig_len = int.from_bytes(data[:4], "big")
        bit_len = int.from_bytes(data[4:8], "big")
        payload = data[8:]

        bits = self._unpack(payload)[:bit_len]

        node = self.root
        i = 0
        out = bytearray()

        while len(out) < orig_len:
            if node.is_leaf():
                if node.symbol == "NYT":
                    if i + 8 > len(bits):
                        break
                    byte = 0
                    for _ in range(8):
                        byte = (byte << 1) | bits[i]
                        i += 1
                    out.append(byte)
                    self._process(byte)
                else:
                    out.append(node.symbol)
                    self._process(node.symbol)

                node = self.root
            else:
                if i >= len(bits):
                    break
                node = node.left if bits[i] == 0 else node.right
                i += 1

        return out.decode("utf-8", errors="ignore")

    # stats
    def get_compression_stats(self, text: str) -> dict:
        encoded = self.encode(text)
        original = len(text.encode("utf-8"))
        compressed = len(encoded)

        return {
            "original_size": original,
            "compressed_size": compressed,
            "compression_ratio": round(compressed / original, 2) if original else 0,
            "entropy": self._entropy(text)
        }