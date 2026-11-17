import json, base64, gzip, struct

HAR = '/Users/sigal/Downloads/lumen-tap-20260730-092950.har'


def read_varint(b, i):
    shift = 0; result = 0
    while True:
        byte = b[i]; i += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result, i


def parse_pb(b):
    out = {}; i = 0; n = len(b)
    while i < n:
        try:
            tag, i = read_varint(b, i)
        except Exception:
            break
        field = tag >> 3; wire = tag & 0x7
        try:
            if wire == 0:
                val, i = read_varint(b, i)
            elif wire == 1:
                val = b[i:i+8]; i += 8
            elif wire == 2:
                ln, i = read_varint(b, i); val = b[i:i+ln]; i += ln
            elif wire == 5:
                val = b[i:i+4]; i += 4
            else:
                break
        except Exception:
            break
        out.setdefault(field, []).append((wire, val))
    return out


def get(d, f):
    return d.get(f, [None])[0]


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


def classify(jtxt):
    try:
        obj = json.loads(jtxt)
    except Exception:
        return 'json-parse-fail', None
    role = obj.get('role')
    types = []
    ids = []
    if isinstance(obj.get('content'), list):
        for p in obj['content']:
            if isinstance(p, dict):
                types.append(p.get('type'))
                if p.get('type') in ('tool-call', 'tool-result'):
                    ids.append(p.get('toolCallId'))
    return f"{role}:{'/'.join(t for t in types if t)}", ids


h = json.load(open(HAR))
entries = h['log']['entries']

for eidx, e in enumerate(entries):
    if 'RunSSE' not in e['request']['url']:
        continue
    print(f'\n########## RunSSE entry {eidx} ##########')
    raw = base64.b64decode(e['response']['content']['text'])
    for fidx, payload in enumerate(parse_frames(raw)):
        top = parse_pb(payload)
        # field 4 = history/checkpoint envelope
        if 4 in top:
            for wire, val in top[4]:
                if wire != 2:
                    continue
                d4 = parse_pb(val)
                num = get(d4, 1)          # 4.1 = message number
                # 4.3 = message wrapper; 4.3.2 = json OR 4.3.4 = json
                desc = ''
                ids = None
                if 3 in d4:
                    for w3, v3 in d4[3]:
                        if w3 != 2:
                            continue
                        d43 = parse_pb(v3)
                        for jf in (2, 4):
                            if jf in d43:
                                for wj, vj in d43[jf]:
                                    if wj == 2:
                                        try:
                                            s = vj.decode('utf-8')
                                        except Exception:
                                            continue
                                        if s.startswith('{'):
                                            desc, ids = classify(s)
                if desc:
                    print(f'  frame {fidx}: 4.1(num)={num}  -> {desc}  ids={ids}')
