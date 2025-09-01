import duvc_ctl, pytest

def test_list_devices_and_find():
    devices = duvc_ctl.list_devices()
    assert isinstance(devices, list)
    if not devices:
        pytest.skip("no UVC devices connected")

    dev = devices[0]
    assert isinstance(dev.name, str)
    assert isinstance(dev.path, str)

    found = duvc_ctl.find_device_by_name(dev.name)
    assert found is not None
    assert found.path == dev.path

def test_get_device_info():
    devices = duvc_ctl.list_devices()
    if not devices:
        pytest.skip("no UVC devices connected")

    info = duvc_ctl.get_device_info(devices[0])
    assert "name" in info
    assert "camera_properties" in info
    assert "video_properties" in info
