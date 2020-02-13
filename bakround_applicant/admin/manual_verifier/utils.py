__author__ = "natesymer"

import json
from django.views import View
from bakround_applicant.utilities.functions import json_result
from bakround_applicant.models.db import ProfileEmail, ProfilePhoneNumber

def vector_diff_param_update_model(cls, profile, vec):
    """Apply batch updates to emails and phone numbers from the frontend."""
    for d in vec:
        if d.get('old_value') == d.get('new_value'): continue

        if 'old_value' in d:
            cls.objects.filter(value=d['old_value'], profile_id=profile.id).delete()

        if 'new_value' in d:
            cls(value=d['new_value'], profile=profile).save()



def profile_to_json(profile):
    return {
        "id": profile.id,
        "first_name": profile.first_name,
        "middle_name": profile.middle_name,
        "last_name": profile.last_name,
        "street_address": profile.street_address,
        "summary": profile.summary,
        "emails": list(ProfileEmail.all_sane().filter(profile_id=profile.id).values_list("value", flat=True)),
        "phones": list(ProfilePhoneNumber.all_sane().filter(profile_id=profile.id).values_list("value", flat=True))
    }

def pvr_to_status_json(r):
    return {
        "contacted": r.contacted,
        "responded": r.responded,
        "unreachable": r.unreachable,
        "pending_action": r.pending_action,
        "broken": r.broken,
        "verified": r.verified
    }

def profile_from_params(params):
    if 'request_id' in params:
        try:    return ProfileVerificationRequest.objects.get(id=int(params.get('request_id'))).profile
        except: pass
    
    if 'profile_id' in params:
        try: return Profile.objects.get(id=int(params.get('profile_id')))
        except: pass

    return None

class JSONView(View):
    def go(self, request, params):
        raise NotImplemented

    @json_result
    def get(self, request):
        return self.go(request, request.GET)

    @json_result
    def post(self, request):
        try:
            params = json.loads(request.body.decode('utf8'))
        except:
            params = {}
        return self.go(request, params)

