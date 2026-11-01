from registry_path.logic import _format
import winreg

def test_registry_format_includes_type_and_value():
    assert _format("value", winreg.REG_SZ) == "REG_SZ\nvalue\n"
