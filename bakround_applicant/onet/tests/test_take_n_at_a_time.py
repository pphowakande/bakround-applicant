
import pytest
from bakround_applicant.utilities.functions import take_n_at_a_time


def test_take_n_at_a_time():
    assert list(take_n_at_a_time(3, [1, 2, 3, 4, 5, 6, 7])) == [[1, 2, 3], [4, 5, 6], [7]]

    assert list(take_n_at_a_time(3, [])) == []

    # If the length of the list is a multiple of n, there should not be an empty group
    #       at the end.
    assert list(take_n_at_a_time(4, [1, 2, 3, 4])) == [[1, 2, 3, 4]]

    # test with an iterator
    R = range(11, -1, -1)
    generator = take_n_at_a_time(5, R)
    assert next(generator) == [11, 10, 9, 8, 7]
    assert next(generator) == [6, 5, 4, 3, 2]
    assert next(generator) == [1, 0]
    # calling next() now should fail because there are no more results
    with pytest.raises(StopIteration):
        next(generator)
