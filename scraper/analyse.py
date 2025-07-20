from collections import Counter
import re

def analyze_headers(headers):
    all_words = re.findall(r'\b\w+\b', " ".join(headers).lower())
    word_count = Counter(all_words)
    repeated_words = {word: count for word, count in word_count.items() if count > 2}
    return repeated_words