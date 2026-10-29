from creator_delivery import Delivery, run_delivery


def test_processing_failure_keeps_delivery_for_review(monkeypatch):
    events = []
    monkeypatch.setattr("creator_delivery.infrai.account.whoami", lambda: {"id": "account-1"})
    monkeypatch.setattr("creator_delivery.infrai.logs.ingest", lambda **event: events.append(event["entries"][0]))
    job = Delivery("order-9", "creator-2", "subscriber-4", "asset-8")

    result = run_delivery(job, lambda _asset: (_ for _ in ()).throw(ValueError("bad source")))

    assert result == {"order_id": "order-9", "status": "needs_review"}
    assert [event["message"] for event in events] == ["delivery_started", "content_processing_failed"]
