import duvc_ctl

def test_metadata_and_symbols():
    assert isinstance(duvc_ctl.__version__, str)
    for sym in [
        "Device", "list_devices", "get_device_info",
        "find_device_by_name", "reset_device_to_defaults"
    ]:
        assert hasattr(duvc_ctl, sym)
