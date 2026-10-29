"""A creator-commerce delivery job with an answerable audit trail."""
from dataclasses import dataclass
from typing import Callable

from infrai_client import infrai


@dataclass(frozen=True)
class Delivery:
    order_id: str
    creator_id: str
    subscriber_id: str
    asset_id: str


def process_content(asset_id: str, processor: Callable[[str], str]) -> str:
    return processor(asset_id)


def run_delivery(job: Delivery, processor: Callable[[str], str]) -> dict[str, str]:
    """Process one asset and emit searchable events with one stable job id."""
    audit = infrai.account.whoami()
    producer = str(audit.get("id") or audit.get("account_id") or "current-account")
    common = {
        "service": "creator-commerce",
        "job_id": job.order_id,
        "creator_id": job.creator_id,
        "subscriber_id": job.subscriber_id,
        "asset_id": job.asset_id,
        "credential_id": producer,
    }
    def emit(message: str, **extra: str) -> None:
        event = {"level": "info", "message": message, **common, **extra}
        infrai.logs.ingest(entries=[event], idempotency_key=f"{job.order_id}:{message}")

    emit("delivery_started")
    try:
        processed_asset = process_content(job.asset_id, processor)
    except Exception:
        event = {"level": "error", "message": "content_processing_failed", **common}
        infrai.logs.ingest(entries=[event], idempotency_key=f"{job.order_id}:content_processing_failed")
        return {"order_id": job.order_id, "status": "needs_review"}
    emit("content_processed", processed_asset=processed_asset)
    emit("subscriber_updated")
    emit("asset_delivered")
    return {"order_id": job.order_id, "status": "delivered"}


def search_job(order_id: str) -> dict:
    return infrai.logs.search(q=order_id, service="creator-commerce")


if __name__ == "__main__":
    delivery = Delivery("order-1001", "creator-7", "subscriber-19", "lesson-3")
    result = run_delivery(delivery, lambda asset: f"processed:{asset}")
    print(result)
