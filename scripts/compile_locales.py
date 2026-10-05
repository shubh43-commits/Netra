"""
Utility script to compile gettext .po files to .mo binary catalogs
without requiring external GNU gettext binaries on Windows.
"""
import struct
import os
import re

def compile_po_to_mo(po_path, mo_path):
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Matches msgid and msgstr pairs, handling multiline quoted strings
    pattern = re.compile(
        r'msgid\s+((?:"(?:[^"\\]|\\.)*"\s*)+)\s+msgstr\s+((?:"(?:[^"\\]|\\.)*"\s*)+)'
    )

    def clean_str(raw):
        lines = re.findall(r'"((?:[^"\\]|\\.)*)"', raw)
        text = ''.join(lines)
        # Decode common escape sequences safely
        return (text.replace(r'\"', '"')
                    .replace(r'\n', '\n')
                    .replace(r'\t', '\t')
                    .replace(r'\\', '\\'))

    entries = []
    for match in pattern.finditer(content):
        orig = clean_str(match.group(1))
        trans = clean_str(match.group(2))
        entries.append((orig, trans))

    # Sort entries by msgid
    entries.sort(key=lambda x: x[0].encode('utf-8'))

    count = len(entries)
    orig_table = []
    trans_table = []

    keystart = 28 + (count * 8) + (count * 8)

    orig_bytes_list = [e[0].encode('utf-8') + b'\x00' for e in entries]
    trans_bytes_list = [e[1].encode('utf-8') + b'\x00' for e in entries]

    curr_offset = keystart
    for b in orig_bytes_list:
        orig_table.append((len(b) - 1, curr_offset))
        curr_offset += len(b)

    for b in trans_bytes_list:
        trans_table.append((len(b) - 1, curr_offset))
        curr_offset += len(b)

    output = bytearray()
    # Magic number for gettext .mo file in native / standard format
    output.extend(struct.pack('<I', 0x950412de))
    # Format revision
    output.extend(struct.pack('<I', 0))
    # Number of strings
    output.extend(struct.pack('<I', count))
    # Offset of original strings table
    output.extend(struct.pack('<I', 28))
    # Offset of translation strings table
    output.extend(struct.pack('<I', 28 + (count * 8)))
    # Hash table size
    output.extend(struct.pack('<I', 0))
    # Hash table offset
    output.extend(struct.pack('<I', 0))

    # Original strings table
    for length, offset in orig_table:
        output.extend(struct.pack('<II', length, offset))

    # Translated strings table
    for length, offset in trans_table:
        output.extend(struct.pack('<II', length, offset))

    # Actual string payloads
    for b in orig_bytes_list:
        output.extend(b)
    for b in trans_bytes_list:
        output.extend(b)

    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, 'wb') as f:
        f.write(output)
    print(f"Successfully compiled {po_path} -> {mo_path} ({count} entries, {len(output)} bytes)")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    po_en = os.path.join(base_dir, 'locale', 'en', 'LC_MESSAGES', 'django.po')
    mo_en = os.path.join(base_dir, 'locale', 'en', 'LC_MESSAGES', 'django.mo')
    po_hi = os.path.join(base_dir, 'locale', 'hi', 'LC_MESSAGES', 'django.po')
    mo_hi = os.path.join(base_dir, 'locale', 'hi', 'LC_MESSAGES', 'django.mo')

    compile_po_to_mo(po_en, mo_en)
    compile_po_to_mo(po_hi, mo_hi)
