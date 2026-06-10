from eval.scoring import clamp_score


def test_clamp_score() -> None:
    assert clamp_score(-1) == 0
    assert clamp_score(82) == 82
    assert clamp_score(101) == 100
