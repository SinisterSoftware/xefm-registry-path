"""reg:// の一覧に出す列 (型・データのプレビュー)。"""

import winreg

from xefm.user_api import Cell

from .logic import DEFAULT, HIVES, _TYPES, _open

PREVIEW = 60


def in_reg(path):
    return str(path).startswith("reg://")


def _key_of(directory):
    return str(directory)[len("reg://"):].strip("/")


def _scan(directory):
    """(サブキー名の集合, {値名: (値, 型)})。ハイブ一覧や開けないキーは空。"""
    key_path = _key_of(directory)
    if not key_path:
        return set(HIVES), {}
    key = _open(key_path)
    if key is None:
        return set(), {}
    subs, values = set(), {}
    with key:
        n_sub, n_val, _ = winreg.QueryInfoKey(key)
        for i in range(n_sub):
            try:
                subs.add(winreg.EnumKey(key, i))
            except OSError:
                break
        for i in range(n_val):
            try:
                name, value, typ = winreg.EnumValue(key, i)
            except OSError:
                break
            values[(name or DEFAULT).replace("/", "∕")] = (value, typ)
    return subs, values


def _read(directory, entries, getter):
    try:
        subs, values = _scan(directory)
    except Exception:
        return [None] * len(entries)
    out = []
    for e in entries:
        name = e.path.name
        if name in subs:
            out.append(getter(None, None, True))
        elif name in values:
            out.append(getter(*values[name], False))
        else:
            out.append(None)
    return out


def _type(value, typ, is_key):
    return "<KEY>" if is_key else _TYPES.get(typ, str(typ)).replace("REG_", "")


def _preview(value, typ, is_key):
    if is_key:
        return ""
    if typ == winreg.REG_MULTI_SZ:
        body = " | ".join(value or [])
    elif typ in (winreg.REG_BINARY, winreg.REG_NONE) or isinstance(value, bytes):
        body = (value or b"").hex(" ")
    elif isinstance(value, int):
        body = f"0x{value:x} ({value})"
    else:
        body = str(value).replace("\r", " ").replace("\n", " ")
    return body if len(body) <= PREVIEW else body[:PREVIEW - 1] + "…"


def reg_type(directory, entries):
    return _read(directory, entries, _type)


def reg_data(directory, entries):
    return _read(directory, entries, _preview)


def fmt_type(value, entry):
    if not value:
        return ""
    return Cell(value, color="accent") if value == "<KEY>" else Cell(value, color="muted")
