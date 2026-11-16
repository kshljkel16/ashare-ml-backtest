"""Step 6 — the provided LLM parser (passes from the start; read it)."""
import json

from qml.llm import TitleClassifier, parse_response, Response


def test_parse_valid_fenced_and_index_matched():
    text = 'ok ```json [{"i": 2, "sentiment": -1, "event": "penalty"}, {"i": 1, "sentiment": 1, "event": "BUYBACK"}] ```'
    a, b = parse_response(text, 2)
    assert (a.sentiment, a.event) == (1, "buyback")
    assert (b.sentiment, b.event) == (-1, "penalty")


def test_parse_rejects_bad_values():
    text = json.dumps([{"i": 1, "sentiment": 5, "event": "x"}, {"i": 2, "sentiment": 0, "event": "made_up"}])
    a, b, c = parse_response(text, 3)
    assert a.sentiment is None                       # invalid sentiment
    assert (b.sentiment, b.event) == (0, "routine")  # unknown event -> routine
    assert c.sentiment is None                       # missing item
    assert parse_response("sorry", 2)[1].sentiment is None


class Fake:
    calls = 0

    def complete(self, system, user):
        Fake.calls += 1
        n = len(user.splitlines())
        return Response(json.dumps([{"i": i, "sentiment": 1, "event": "buyback"} for i in range(1, n + 1)]), 100, 20)


def test_classifier_batches_and_caches(tmp_path):
    Fake.calls = 0
    clf = TitleClassifier(Fake(), batch_size=2, price_in=1, price_out=1, cache_path=tmp_path / "c.json")
    labels = clf.classify(["a", "b", "c"])
    assert Fake.calls == 2 and all(l.sentiment == 1 for l in labels)
    assert sum(l.cost_usd for l in labels) > 0
    TitleClassifier(Fake(), cache_path=tmp_path / "c.json").classify(["a", "b", "c"])
    assert Fake.calls == 2                           # all from cache
