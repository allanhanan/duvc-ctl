import duvc_ctl, uuid, pytest

def test_vendor_property_roundtrip():
    devices = duvc_ctl.list_devices()
    if not devices:
        pytest.skip("no UVC devices connected")

    dev = devices[0]
    guid = duvc_ctl.guid_from_uuid(uuid.UUID("{6bdd1fc6-810f-11d0-bec7-08002be2092f}"))

    payload = b"\x01\x02\x03\x04"
    ok = duvc_ctl.write_vendor_property(dev, guid, 1, payload)
    assert isinstance(ok, bool)

    ok, data = duvc_ctl.read_vendor_property(dev, guid, 1)
    assert isinstance(ok, bool)
    assert isinstance(data, (bytes, bytearray))
