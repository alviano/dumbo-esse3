from dumbo_esse3.primitives import DateTime


def test_exam_date_time_order():
    assert DateTime.now() <= DateTime.now()
