import json, base64, gzip, struct, re

HAR = '/Users/sigal/Downloads/lumen-tap-20260730-092950.har'


def parse_frames(raw):
    frames = []; i = 0
    while i + 5 <= len(raw):
        flag = raw[i]; ln = struct.unpack('>I', raw[i+1:i+5])[0]
        payload = raw[i+5:i+5+ln]
        if flag & 0x01:
            try:
                payload = gzip.decompress(payload)
            except Exception:
                pass
        frames.append(payload); i += 5 + ln
    return frames


def extract_json_objects(text):
    """Find balanced {...} JSON objects in a string."""
    objs = []
    depth = 0; start = None; instr = False; esc = False
    for idx, ch in enumerate(text):
        if esc:
            esc = False; continue
        if ch == '\\':
            esc = True; continue
        if ch == '"':
            instr = not instr
        if instr:
            continue
        if ch == '{':
            if depth == 0:
                start = idx
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    objs.append(text[start:idx+1])
                    start = None
    return objs


h = json.load(open(HAR))
entries = h['log']['entries']

tool_calls = []
tool_results = []

for eidx, e in enumerate(entries):
    if 'RunSSE' not in e['request']['url']:
        continue
    raw = base64.b64decode(e['response']['content']['text'])
    for payload in parse_frames(raw):
        # scan raw payload for utf-8 json fragments
        try:
            text = payload.decode('utf-8', errors='ignore')
        except Exception:
            continue
        for pos in [m.start() for m in re.finditer(r'\{"', text)]:
            for cand in extract_json_objects(text[pos:pos+200000])[:1]:
                try:
                    obj = json.loads(cand)
                except Exception:
                    continue
                # look for message objects with content arrays
                if isinstance(obj, dict) and isinstance(obj.get('content'), list):
                    for part in obj['content']:
                        if not isinstance(part, dict):
                            continue
                        if part.get('type') == 'tool-call':
                            tool_calls.append((eidx, obj.get('role'), part))
                        elif part.get('type') == 'tool-result':
                            tool_results.append((eidx, obj.get('role'), part))

print('=== TOOL CALLS ===', len(tool_calls))
seen = set()
for eidx, role, p in tool_calls:
    key = p.get('toolCallId')
    if key in seen:
        continue
    seen.add(key)
    print('keys:', list(p.keys()))
    print('  toolName:', p.get('toolName'), '| toolCallId:', p.get('toolCallId'))
    for k, v in p.items():
        if k not in ('args', 'toolName', 'toolCallId', 'type'):
            print('   extra field:', k, '=', repr(v)[:200])

print()
print('=== TOOL RESULTS ===', len(tool_results))
seen = set()
for eidx, role, p in tool_results:
    key = p.get('toolCallId')
    if key in seen:
        continue
    seen.add(key)
    print('keys:', list(p.keys()))
    for k, v in p.items():
        if k not in ('output', 'result',):
            print('   field:', k, '=', repr(v)[:200])
