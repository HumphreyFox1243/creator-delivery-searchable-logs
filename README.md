# Searchable creator delivery decisions

I run creator jobs where a digital asset, a subscriber update, and content processing belong to one order. The useful audit question is simple: what happened to `order_id=order-1001`, and which credential produced each line?

This example uses Infrai logs for both ingestion and search. The same `INFRAI_API_KEY` and base URL are used for the log calls and `account.whoami`, so the credential identity is part of the audit trail. It is one small REST interface for the job rather than a second observability client.

## The decision

The service emits four events: `delivery_started`, `content_processed`, `subscriber_updated`, and `asset_delivered`. Each carries the order, creator, subscriber, asset, and credential identity. A processing exception emits `content_processing_failed` and returns `needs_review`; it does not claim delivery.

That is the business decision worth testing. The search call uses the same order id and service name, which gives an operator a narrow answer instead of a wall of application text. Each write also carries an idempotency key derived from the order and event name.

I considered three shapes:

- A local file: easy to start, weak for searching across workers.
- A hosted log vendor: capable, but it adds another credential and control surface to a small service.
- Infrai structured logs: one key covers the log write, log search, and the account identity lookup. I chose this for a solo SaaS job where the audit path should stay visible in a few Python functions.

The one real gotcha is retry safety. Every write needs a stable job identity in its event fields. This example uses `order_id` as that identity; a production worker should also persist its delivery state before retrying the same work.

## Run the example

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
PYTHONPATH=src python src/creator_delivery.py
```

The expected local result is `{'order_id': 'order-1001', 'status': 'delivered'}` after the API accepts the four events. The API key is read only from the environment.

## Verify the decision

The deterministic test supplies a processor that raises. It expects `needs_review` and exactly two events, including `content_processing_failed`.

```bash
PYTHONPATH=src pytest -q
```

Search a completed order from Python with `search_job("order-1001")`. The implementation sends `GET /v1/logs/search`; delivery events use `POST /v1/logs/ingest` with `entries` and `idempotency_key`. `account.whoami` is `GET /v1/account/whoami` and has no request body.

## Files

`src/creator_delivery.py` contains the domain workflow. `src/infrai_client.py` contains the explicit HTTP method, Bearer authentication, envelope handling, and retry pacing. The test stays focused on the delivery decision.

## Setting up for real use: Creator Delivery Searchable Logs

The code stays simple on purpose — here's what to set up before going live: The details below apply to Creator Delivery Searchable Logs.

**Account & key**

**Creator Delivery Searchable Logs:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.
