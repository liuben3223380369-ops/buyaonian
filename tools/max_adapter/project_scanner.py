#!/usr/bin/env python3
# MAX Android source adapter scanner
# Detects Android project structure for localization injection.

import os

TARGETS = [
    "settings.gradle",
    "build.gradle",
    "app/src/main/res",
    "AndroidManifest.xml"
]


def scan(root):
    result = {}
    for target in TARGETS:
        result[target] = os.path.exists(os.path.join(root, target))
    return result


if __name__ == '__main__':
    import json
    print(json.dumps(scan('.'), ensure_ascii=False, indent=2))
