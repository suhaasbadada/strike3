import json
import random
import string
import math

try:
    from app.services.adaptive_huffman import AdaptiveHuffman
except ModuleNotFoundError:
    from services.adaptive_huffman import AdaptiveHuffman

# basic
def test_basic():
    ah = AdaptiveHuffman()

    text = "hello world"

    encoded = ah.encode(text)
    tree = ah.export_tree()
    decoded = ah.decode(encoded)

    print("\noriginal:", text)
    print("encoded :", encoded)
    print("decoded :", decoded)
    print("tree nodes:", len(tree["nodes"]))
    print("tree edges:", len(tree["edges"]))
    print("tree:")
    print(json.dumps(tree, indent=2, ensure_ascii=False))

    assert text == decoded
    assert "nodes" in tree and "edges" in tree
    assert isinstance(tree["nodes"], list)
    assert isinstance(tree["edges"], list)
    print("basic test passed")

# edge cases - emojis, empty string, white and tab spaces
def test_edge_cases():
    cases = [
        "",
        "a",
        "aaaaaa",
        "abcdefg",
        "     ",
        "\n\t\n\t",
        "🙂🙂🙂🙂",
        "hello🙂world🌍",
        "A" * 1000,
    ]

    for case in cases:
        ah = AdaptiveHuffman()
        encoded = ah.encode(case)
        decoded = ah.decode(encoded)

        print(f"[edge] {repr(case[:30])} -> match:", decoded == case)
        assert decoded == case

    print("edge cases passed")

# paragraph test
def test_random_paragraph():
    ah = AdaptiveHuffman()

    text = """
        At Indiana University Bloomington’s Luddy School of Informatics, Computing, and Engineering, 
        the Master of Science in Computer Science program prepares students to lead in modern 
        technology fields such as artificial intelligence, machine learning, big data, and cybersecurity. 
        The curriculum is designed to build both strong theoretical foundations and practical engineering skills,
        allowing students to work across the full computing stack including software systems, operating systems, and hardware-level design. 
        Through hands-on projects and research opportunities, students gain experience in building scalable and secure applications while working closely with faculty and industry-aligned mentors. 
        Graduates of the program often move into high-demand roles such as software engineering, AI engineering, data science, and systems development at leading companies including Amazon, Microsoft, and Meta.
    """

    text = text.strip()

    encoded = ah.encode(text)
    decoded = ah.decode(encoded)

    print("\nrandom paragraph test")
    print("original length:", len(text))
    print("encoded bytes  :", len(encoded))
    print("match          :", decoded == text)

    assert decoded == text

    stats = ah.get_compression_stats(text)
    print("stats:", stats)

    print("random paragraph test passed")

# fuzz test
def test_randomized():
    chars = string.ascii_letters + string.digits + "     "

    for _ in range(20):
        ah = AdaptiveHuffman()

        text = "".join(
            random.choice(chars)
            for _ in range(random.randint(10, 500))
        )

        encoded = ah.encode(text)
        decoded = ah.decode(encoded)

        assert decoded == text

    print("randomized fuzz test passed")

# stability
def test_stability():
    ah = AdaptiveHuffman()

    text = "adaptive huffman stability check"

    for _ in range(10):
        encoded = ah.encode(text)
        decoded = ah.decode(encoded)
        assert text == decoded

    print("stability test passed")

# repeated roundtrip test
def test_repeated_roundtrip():
    ah = AdaptiveHuffman()

    text = "the quick brown fox jumps over the lazy dog"

    for _ in range(50):
        encoded = ah.encode(text)
        decoded = ah.decode(encoded)
        assert decoded == text

    print("repeated roundtrip test passed")

# unicode + mixed stress test
def test_unicode_mixed_stress():
    ah = AdaptiveHuffman()

    text = (
        "hello🙂world🌍\n\t"
        + "ASCII text " * 50
        + "汉字漢字"
        + "🔥🔥🔥"
    )

    encoded = ah.encode(text)
    decoded = ah.decode(encoded)

    assert decoded == text
    print("unicode mixed stress test passed")

# compression sanity test
def test_compression_sanity():
    ah = AdaptiveHuffman()

    text = "aaaaabbbbcccdde"

    stats = ah.get_compression_stats(text)

    # entropy sanity check
    assert stats["entropy"] < 3.0

    # only structural checks (NOT strict compression expectation)
    assert stats["original_size"] > 0
    assert stats["compressed_size"] > 0

    print("compression sanity test passed")

# entropy distribution test
def test_entropy_uniform_distribution():
    ah = AdaptiveHuffman()

    text = "".join(chr(i % 256) for i in range(2000))

    stats = ah.get_compression_stats(text)

    assert stats["entropy"] > 7.0

    print("entropy uniform distribution test passed")

# compression benchmarks
def benchmark_samples():
    samples = [
        ("tiny", "hello world"),
        ("small-repeat", "hello world " * 20),
        ("medium-repeat", "adaptive huffman compression demo " * 200),
        ("large-repeat", ("lorem ipsum dolor sit amet, " * 1000).strip()),
    ]

    print("\ncompression benchmark")
    print("-" * 85)
    print(f"{'name':14} {'entropy':10} {'original':10} {'compressed':12} {'ratio':8} {'wins?':8}")
    print("-" * 85)

    for name, text in samples:
        ah = AdaptiveHuffman()

        encoded = ah.encode(text)
        decoded = ah.decode(encoded)

        assert decoded == text

        stats = ah.get_compression_stats(text)

        wins = "yes" if stats["compressed_size"] < stats["original_size"] else "no"

        print(
            f"{name:14} {stats['entropy']:10.3f} {stats['original_size']:10d} "
            f"{stats['compressed_size']:12d} {stats['compression_ratio']:8.2f} {wins:8}"
        )

    print("-" * 85)

if __name__ == "__main__":
    test_basic()
    test_edge_cases()
    test_random_paragraph()
    test_randomized()
    test_stability()

    # robustness tests
    test_repeated_roundtrip()
    test_unicode_mixed_stress()
    test_compression_sanity()
    test_entropy_uniform_distribution()

    benchmark_samples()