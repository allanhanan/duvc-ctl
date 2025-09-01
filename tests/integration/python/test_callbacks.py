import duvc_ctl, pytest

def test_device_change_callback(monkeypatch):
    if not duvc_ctl.list_devices():
        pytest.skip("no UVC devices connected")

    called = {}

    def cb(event_type, dev):
        called["event"] = (event_type, dev)

    duvc_ctl.register_device_change_callback(cb)
    # ensure registration doesn’t crash
    duvc_ctl.unregister_device_change_callback()   # <-- no args
