def _login(client, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_wechat_bind_and_login(client):
    admin_headers = _login(client, "admin", "admin123456")
    create_user_response = client.post(
        "/api/v1/users",
        json={
            "username": "device_user_01",
            "password": "device12345",
            "role": "device_user",
        },
        headers=admin_headers,
    )
    assert create_user_response.status_code == 201

    user_headers = _login(client, "device_user_01", "device12345")
    bind_response = client.post(
        "/api/v1/auth/wechat-bind",
        json={"wechat_open_id": "wx-openid-user-01", "wechat_union_id": "wx-union-user-01"},
        headers=user_headers,
    )
    assert bind_response.status_code == 200
    bind_body = bind_response.json()
    assert bind_body["username"] == "device_user_01"
    assert bind_body["wechat_open_id"] == "wx-openid-user-01"
    assert bind_body["wechat_bound_at"] is not None

    wechat_login_response = client.post(
        "/api/v1/auth/wechat-login",
        json={"wechat_open_id": "wx-openid-user-01"},
    )
    assert wechat_login_response.status_code == 200
    token = wechat_login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["username"] == "device_user_01"
    assert me_body["wechat_bound"] is True


def test_notification_subscription_status_roundtrip(client):
    headers = _login(client, "admin", "admin123456")

    initial_status_response = client.get(
        "/api/v1/notifications/subscription-status",
        headers=headers,
    )
    assert initial_status_response.status_code == 200
    assert initial_status_response.json()["enabled"] is False

    subscribe_response = client.post(
        "/api/v1/notifications/subscribe",
        json={
            "template_ids": ["tmpl_alarm_triggered", "tmpl_alarm_recovered"],
            "source": "wechat-miniprogram",
        },
        headers=headers,
    )
    assert subscribe_response.status_code == 200
    subscribe_body = subscribe_response.json()
    assert subscribe_body["enabled"] is True
    assert subscribe_body["template_ids"] == [
        "tmpl_alarm_triggered",
        "tmpl_alarm_recovered",
    ]
    assert subscribe_body["subscribed_at"] is not None

    status_response = client.get(
        "/api/v1/notifications/subscription-status",
        headers=headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["enabled"] is True

    unsubscribe_response = client.post(
        "/api/v1/notifications/unsubscribe",
        headers=headers,
    )
    assert unsubscribe_response.status_code == 200
    unsubscribe_body = unsubscribe_response.json()
    assert unsubscribe_body["enabled"] is False
    assert unsubscribe_body["unsubscribed_at"] is not None


def test_alarm_notification_dispatch_job(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "WECHAT_ENABLED", True)
    monkeypatch.setattr(settings, "WECHAT_SUBSCRIBE_TEMPLATE_ID", "tmpl_alarm_demo")

    async def fake_send_subscribe_message(openid, template_id, data, page=None):
        assert openid == "wx-openid-admin"
        assert template_id == "tmpl_alarm_demo"
        assert isinstance(data, dict)
        return {"errcode": 0, "errmsg": "ok", "msgid": 1001}

    monkeypatch.setattr(
        "app.services.notification_service.send_subscribe_message",
        fake_send_subscribe_message,
    )

    admin_headers = _login(client, "admin", "admin123456")
    bind_response = client.post(
        "/api/v1/auth/wechat-bind",
        json={"wechat_open_id": "wx-openid-admin"},
        headers=admin_headers,
    )
    assert bind_response.status_code == 200

    subscribe_response = client.post(
        "/api/v1/notifications/subscribe",
        json={"template_ids": ["tmpl_alarm_demo"]},
        headers=admin_headers,
    )
    assert subscribe_response.status_code == 200

    create_device_response = client.post(
        "/api/v1/devices",
        json={"name": "wechat-alarm-device", "serial_number": "WX-ALARM-001"},
        headers=admin_headers,
    )
    assert create_device_response.status_code == 201
    device_id = create_device_response.json()["id"]

    add_module_response = client.post(
        f"/api/v1/devices/{device_id}/modules",
        json={"module_code": "A"},
        headers=admin_headers,
    )
    assert add_module_response.status_code == 201
    module_id = add_module_response.json()["modules"][0]["id"]

    create_alarm_response = client.post(
        "/api/v1/alarms",
        json={
            "module_id": module_id,
            "alarm_type": "low_voltage",
            "message": "voltage below threshold",
        },
        headers=admin_headers,
    )
    assert create_alarm_response.status_code == 201
    alarm_body = create_alarm_response.json()
    assert alarm_body["notification_status"] == "pending"

    dispatch_response = client.post(
        "/api/v1/jobs/alarm-notification-dispatch",
        headers=admin_headers,
    )
    assert dispatch_response.status_code == 200
    dispatch_body = dispatch_response.json()
    assert dispatch_body["processed_count"] >= 1
    assert dispatch_body["sent_count"] >= 1

    alarms_response = client.get("/api/v1/alarms", headers=admin_headers)
    assert alarms_response.status_code == 200
    matched_alarm = next(item for item in alarms_response.json() if item["id"] == alarm_body["id"])
    assert matched_alarm["notification_status"] == "sent"
    assert matched_alarm["notification_sent_at"] is not None
