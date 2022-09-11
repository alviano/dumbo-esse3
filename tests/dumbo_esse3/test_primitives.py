from dumbo_esse3.primitives import ExamDateTime


def test_exam_date_time_order():
    assert ExamDateTime.now() <= ExamDateTime.now()
