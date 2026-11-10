"""Persistent offline BGE process; separates incompatible backend dependency graphs."""
import argparse
import json
import os
from pathlib import Path
import sys
from smallville_local_embeddings import LocalEmbeddings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-root', type=Path, required=True)
    parser.add_argument('--receipts', type=Path, required=True)
    args = parser.parse_args()
    encoder = LocalEmbeddings(args.model_root, args.receipts)
    for line in sys.stdin:
        if len(line) > 2 * 1024 * 1024:
            raise ValueError('Oversized embedding request')
        row = json.loads(line)
        texts = row['texts']
        if not isinstance(texts, list) or len(texts) > 256 or any(not isinstance(t, str) for t in texts):
            raise ValueError('Invalid embedding batch')
        result = {'id': row['id'], 'vectors': [encoder(t) for t in texts]}
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
