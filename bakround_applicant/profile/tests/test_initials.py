
__author__ = "tplick"

from bakround_applicant.profile.profile_search import make_initials_for_profile_id


def test_make_initials():
    assert make_initials_for_profile_id(0) == "A. A."
    assert make_initials_for_profile_id(26) == "A. B."
    assert make_initials_for_profile_id(129) == "Z. E."
    assert make_initials_for_profile_id(26*26 - 1) == "Z. Z."
    assert make_initials_for_profile_id(26*26) == "A. A."
