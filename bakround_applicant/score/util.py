__author__ = "natesymer"

import json
import requests
import os
import random
from bakround_applicant.all_models.db import Score
from bakround_applicant.services.queue import QueueConnection, QueueNames
from bakround_applicant.utilities.functions import is_local

class ScoringException(Exception):
    def __init__(self, message, profile_id, job_id):
        super().__init__(message)
        self.profile_id = profile_id
        self.job_id = job_id

class ScoreGenerationException(ScoringException):
    pass

class InvalidScoreRequestException(ScoringException):
    pass

def strict_coerce_int(v):
    """There are 3 kinds of integers: a) `int`s b) `int()`-able things c) fake `int`s (`bool` et al.)
    Only return a & b, as an `int`."""
    if type(v) is int: # This violates PEP8, but we want strictness...
        return v
    if isinstance(v, int): # Now catch all int-likes, like Bool.
        raise ValueError("`{}` is not an integer, strictly speaking.".format(v))
    return int(v)

def get_score_from_score_server(job_id=None, profile_id=None):
    try: job_id = strict_coerce_int(job_id)
    except: raise InvalidScoreRequestException("Invalid job id", job_id=job_id, profile_id=profile_id)

    try: profile_id = strict_coerce_int(profile_id)
    except: raise InvalidScoreRequestException("Invalid profile id", job_id=job_id, profile_id=profile_id)

    # If we're running locally, just return a random score.
    # The scoring infrastructure isn't set up to be used with
    # bakround-applicant locally, and for most testing purposes,
    # it doesn't matter if the scores are applicable.
    if is_local():
        return (random.uniform(350.0, 850.0), -1.0)

    # TODO: check profile_id and job_id for int-ness

    params = json.dumps({
        "applicant_id": profile_id,
        "job_id": job_id,
        "algo_version": "current",
        "database": "applicant"
    })

    scoring_url = os.environ['SCORING_URL']

    try:
        result = requests.get(scoring_url, params=params)
    except:
        raise ScoreGenerationException(message="Failed to call scoring JSON API.",
                                       profile_id=profile_id,
                                       job_id=job_id)

    if result is None or result.status_code is not 200:
        res_txt = result.text if result else None
        raise ScoreGenerationException(message="HTTP error with response: {}".format(res_txt),
                                       profile_id=profile_id,
                                       job_id=job_id)

    result_json = result.json()

    if not result_json.get('success', False):
        reason = result_json.get('reason') or 'Unknown scoring error'
        raise ScoreGenerationException(message=reason, profile_id=profile_id, job_id=job_id)

    if not result_json.get('score_value'):
        raise ScoreGenerationException(message="Score value not specified.", profile_id=profile_id, job_id=job_id)

    return (result_json['score_value'], result_json['algo_version_used'])


def get_score(score_request):
    """Idempotent: requests a score from the algo service
                   and returns an unsaved Score record"""
    score_value, algo_version = get_score_from_score_server(job_id=score_request.job_id,
                                                            profile_id=score_request.profile_id)

    return Score(profile_id=score_request.profile_id,
                 job_id=score_request.job_id,
                 score_value=score_value,
                 algorithm_version=algo_version)

def queue_request(score_request, priority=None, skip_delta_days=None):
    if score_request.id is not None:
        QueueConnection.quick_publish(
            queue_name=QueueNames.scoring_service,
            body=json.dumps({'mode': 'single',
                             'skip_delta_days': skip_delta_days,
                             'score_request_id': score_request.id}),
            priority=priority)


def queue_request_icims(score_request,profile_id, source, profile_resume_id, priority=None, skip_delta_days=None):
    if score_request.id is not None:
        QueueConnection.quick_publish(
            queue_name=QueueNames.scoring_service,
            body=json.dumps({'mode': 'single',
                             'skip_delta_days': skip_delta_days,
                             'score_request_id': score_request.id,
                             'profile_id': profile_id,
                             'source': source,
                             'profile_resume_id':profile_resume_id}),
            priority=priority)

def queue_job_rescore(job_id, skip_delta_days=None):
    print("queue_job_rescore function------------")
    QueueConnection.quick_publish(
        queue_name=QueueNames.scoring_service,
        body=json.dumps({'mode': 'system',
                         'job_id': job_id,
                         'skip_delta_days': skip_delta_days}))

def queue_job_remap(job_id):
    QueueConnection.quick_publish(
        queue_name=QueueNames.mapping_service,
        body=json.dumps({'job_id': job_id}))
