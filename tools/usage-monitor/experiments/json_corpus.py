"""Bounded stdlib iteration over a JSON array; no dataset code execution."""
import json
from pathlib import Path


def array_records(path, chunk_size=65536, max_record_characters=16000000):
    decoder=json.JSONDecoder()
    with Path(path).open(encoding='utf-8') as stream:
        buffer=''; eof=False
        def fill():
            nonlocal buffer,eof
            part=stream.read(chunk_size);buffer+=part;eof=not part
            if len(buffer)>max_record_characters:raise ValueError('JSON record exceeds bound')
        def trim():
            nonlocal buffer
            buffer=buffer.lstrip()
            while not buffer and not eof:fill();buffer=buffer.lstrip()
        fill();trim()
        if not buffer.startswith('['):raise ValueError('Expected JSON array')
        buffer=buffer[1:];trim()
        if buffer.startswith(']'):
            buffer=buffer[1:];trim()
            if buffer:raise ValueError('Trailing JSON data')
            return
        while True:
            trim()
            while True:
                try:value,end=decoder.raw_decode(buffer);break
                except json.JSONDecodeError:
                    if eof:raise
                    fill()
            if not isinstance(value,dict):raise ValueError('Expected JSON object record')
            buffer=buffer[end:];yield value;trim()
            if buffer.startswith(']'):
                buffer=buffer[1:];trim()
                if buffer:raise ValueError('Trailing JSON data')
                return
            if not buffer.startswith(','):raise ValueError('Expected comma or array end')
            buffer=buffer[1:];trim()
            if buffer.startswith(']'):raise ValueError('Trailing comma')


def select_records(path, ids):
    wanted=set(map(str,ids));found={}
    for row in array_records(path):
        key=str(row['question_id'])
        if key in wanted:
            if key in found:raise ValueError('Duplicate reserved ID')
            found[key]=row
    if set(found)!=wanted:raise ValueError('Missing reserved IDs')
    return found
