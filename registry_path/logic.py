"""reg:// 仮想フォルダ: Windows レジストリの閲覧 (読み取り専用)

キー = フォルダ、値 = ファイル (内容は「型: 値」のテキスト)。
編集は regedit に任せる (アクション regedit-here / Alt-Shift-Q)。
"""
import io
import subprocess
import winreg

from xefm.path_base import ReadOnlyPathImpl, UriStatResult

HIVES = {
    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_USERS": winreg.HKEY_USERS,
    "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
}
DEFAULT = "(Default)"
_TYPES = {
    winreg.REG_NONE: "REG_NONE", winreg.REG_SZ: "REG_SZ",
    winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ", winreg.REG_BINARY: "REG_BINARY",
    winreg.REG_DWORD: "REG_DWORD", winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
    winreg.REG_QWORD: "REG_QWORD",
}
_EPOCH_DIFF = 11644473600  # 1601 → 1970 (秒)


def _split(key):
    hive, _, sub = key.partition("/")
    return hive, sub.replace("/", "\\")


def _open(key):
    hive, sub = _split(key)
    if hive not in HIVES:
        return None
    try:
        return winreg.OpenKey(HIVES[hive], sub, 0, winreg.KEY_READ)
    except OSError:
        return None


def _format(value, typ):
    if typ == winreg.REG_MULTI_SZ:
        body = "\n".join(value or [])
    elif typ in (winreg.REG_BINARY, winreg.REG_NONE) or isinstance(value, bytes):
        body = (value or b"").hex(" ")
    elif isinstance(value, int):
        body = f"{value} (0x{value:x})"
    else:
        body = str(value)
    return f"{_TYPES.get(typ, typ)}\n{body}\n"


def _is_japanese():
    try:
        import ctypes
        return (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x11
    except Exception:
        return False


def _msg(en, ja):
    return ja if _is_japanese() else en


def _computer_label(regedit_key):
    """regedit の LastKey 先頭 (「コンピューター」/「Computer」) は表示言語で変わる。
    前回の値から取り、無ければ表示言語から決める。"""
    import winreg
    try:
        last = winreg.QueryValueEx(regedit_key, "LastKey")[0]
        if last and "\\" in last:
            return last.split("\\", 1)[0]
    except OSError:
        pass
    return "コンピューター" if _is_japanese() else "Computer"


class RegistryPathImpl(ReadOnlyPathImpl):
    """reg://HKEY_CURRENT_USER/Software/... — キーはフォルダ、値はファイル"""

    READ_ONLY_MESSAGE = _msg("The registry is read-only here. Edit it in regedit.",
                             "レジストリはここでは閲覧のみです。編集は regedit で行ってください")

    def _value(self):
        """この パスを親キー配下の「値」として読む。(value, type) または None"""
        parent, _, name = self.key.rpartition("/")
        if not parent:
            return None
        key = _open(parent)
        if key is None:
            return None
        with key:
            try:
                return winreg.QueryValueEx(
                    key, "" if name == DEFAULT else name.replace("∕", "/"))
            except OSError:
                return None

    def exists(self):
        return self.is_dir() or self._value() is not None

    def is_dir(self):
        if not self.key:
            return True
        key = _open(self.key)
        if key is None:
            return False
        key.Close()
        return True

    def iterdir(self):
        if not self.key:
            for name in HIVES:
                yield self.child(name)
            return
        key = _open(self.key)
        if key is None:
            return
        with key:
            n_sub, n_val, _ = winreg.QueryInfoKey(key)
            for i in range(n_sub):
                try:
                    yield self.child(winreg.EnumKey(key, i))
                except OSError:
                    break
            for i in range(n_val):
                try:
                    name = winreg.EnumValue(key, i)[0]
                except OSError:
                    break
                yield self.child((name or DEFAULT).replace("/", "∕"))

    def stat(self):
        if not self.key:
            return UriStatResult(is_dir=True, mtime=0.0)
        key = _open(self.key)
        if key is not None:
            with key:
                ft = winreg.QueryInfoKey(key)[2]
            return UriStatResult(is_dir=True, mtime=ft / 1e7 - _EPOCH_DIFF)
        got = self._value()
        size = len(_format(*got)) if got else 0
        return UriStatResult(size=size, mtime=0.0, is_dir=False)

    def open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        got = self._value()
        if got is None:
            raise FileNotFoundError(self.key)
        text = _format(*got)
        if "b" in mode:
            return io.BytesIO(text.encode(encoding or "utf-8"))
        return io.StringIO(text)


def regedit_here(ctx):
    """カーソル位置のキーを regedit で開く"""
    entry = ctx.pane.focused
    path = str(entry.path if entry is not None else ctx.pane.path)
    if not path.startswith("reg://"):
        ctx.message(_msg("Run this inside reg://", "reg:// の中で実行してください"))
        return
    key = path[len("reg://"):].strip("/")
    if entry is not None and entry.path.is_dir() is False:
        key = key.rpartition("/")[0]
    full = "コンピューター\\" + key.replace("/", "\\")
    try:
        import winreg as w
        with w.CreateKey(w.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Applets\Regedit") as k:
            w.SetValueEx(k, "LastKey", 0, w.REG_SZ, full)
    except OSError:
        pass
    # regedit は管理者権限を要求するので ShellExecute (UAC の確認ダイアログ) で起動する
    import ctypes
    if ctypes.windll.shell32.ShellExecuteW(None, "open", "regedit.exe", None, None, 1) <= 32:
        ctx.message(_msg("Could not start regedit", "regedit を起動できませんでした"))


REGISTRY_SCHEME = {"class": RegistryPathImpl, "override": True}
