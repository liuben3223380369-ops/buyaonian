#!/usr/bin/env python3
# MAX 简体中文汉化自动替换工具
# 方案 A localization pipeline

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MAPPING = os.path.join(ROOT, 'localization', 'zh-rCN', 'ru_to_zh_mapping.json')


def load_mapping():
    with open(MAPPING, 'r', encoding='utf-8') as f:
        return json.load(f)


def translate_text(text, mapping):
    for source, target in mapping.items():
        text = text.replace(source, target)
    return text


def process_file(path, mapping):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = translate_text(content, mapping)
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('translated:', path)


if __name__ == '__main__':
    mapping = load_mapping()
    for root, _, files in os.walk(ROOT):
        for name in files:
            if name.endswith(('.xml', '.json', '.kt', '.java')):
                process_file(os.path.join(root, name), mapping)
