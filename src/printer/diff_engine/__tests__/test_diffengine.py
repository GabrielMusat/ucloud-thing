from ..diffengine import diff


def test_set():
    spec_1 = {"a": {"b": 3}}
    spec_2 = {"a": {"b": 4}}
    d = diff(spec_2, spec_1)
    assert "a" in d
    assert "b" in d["a"]
    assert "$set" in d["a"]["b"]


def test_merge():
    spec_1 = {"a": {"b": 3}}
    spec_2 = {"a": {"c": 4}}
    d = diff(spec_2, spec_1)
    assert "a" in d
    assert "$merge" in d["a"]
    assert "c" in d["a"]["$merge"]
    assert d["a"]["$merge"]["c"] == 4

