
__author__ = "tplick"


from datetime import datetime, timedelta

from bakround_applicant.all_models.db import User, Profile, Score

from .logic import get_database_name


def get_new_user_stats():
    lines = []
    print = (lambda s="": lines.append(s))

    print("Connected to database at {}.".format(get_database_name()))

    # get all the users that were created over the last seven days
    new_users = User.objects.filter(date_joined__gt=datetime.utcnow() - timedelta(days=7)).order_by('date_joined')

    print("{} new users over the past 7 days.".format(new_users.count()))

    for user in new_users:
        try:
            print()

            print("user #{}: {} {}".format(user.id, user.first_name, user.last_name))
            print("registered at {}".format(user.date_joined))

            profile = Profile.objects.get(user=user, queued_for_deletion=False)
            print("job: {}".format(profile.job.job_name))

            score = Score.objects.filter(profile=profile).order_by('-date_created').first()
            score_value = getattr(score, 'score_value', None)
            print("newest score: {}".format(score_value))
        except Exception:
            print("(error)")

    return '\n'.join(lines)
