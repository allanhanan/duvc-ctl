import duvc_ctl, pytest

def test_reset_device_defaults():
    devices = duvc_ctl.list_devices()
    if not devices:
        pytest.skip("no UVC devices connected")

    dev = devices[0]
    results = duvc_ctl.reset_device_to_defaults(dev)
    assert isinstance(results, dict)
    # even if device doesn’t support props, keys exist with bools
    for k, v in results.items():
        assert isinstance(v, bool)
