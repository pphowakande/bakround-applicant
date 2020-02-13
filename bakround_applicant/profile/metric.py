__author__ = "tplick"

from bakround_applicant.all_models.db import ProfileEducation, ProfileExperience, \
                                             ProfileSkill, ProfileCertification

SKILL_REQUIRED_FIELDS = ['skill_name']
SKILL_DETAIL_FIELDS = ['experience_months', 'last_used_date']

EDUCATION_REQUIRED_FIELDS = ['school_name', 'degree_type_id']
EDUCATION_DETAIL_FIELDS = ['degree_date']

EXPERIENCE_REQUIRED_FIELDS = ['company_name', 'position_title', 'start_date']
EXPERIENCE_DETAIL_FIELDS = ['position_description', 'city', 'state_id']

CERTIFICATION_REQUIRED_FIELDS = ['certification_name', 'issued_date']

# return an integer from 0 to 100
def calculate_completeness_metric_and_hints(profile):
    total = 0.0
    hints = {"error": [], "detail": [], "add": []}

    ### Skills

    skills = ProfileSkill.objects.filter(profile=profile)
    if skills.exists():
        total += 20.0

        if are_fields_complete_for_profile(skills, SKILL_REQUIRED_FIELDS):
            total += 10.0
        else:
            hints["error"].append("skill")

        if are_fields_complete_for_profile(skills, SKILL_DETAIL_FIELDS):
            total += 3.34
        else:
            hints["detail"].append("skill")
    else:
        hints["add"].append("skill")




    ### Education

    education = ProfileEducation.objects.filter(profile=profile)
    if education.exists():
        total += 20.0

        if are_fields_complete_for_profile(education, EDUCATION_REQUIRED_FIELDS):
            total += 10.0
        else:
            hints["error"].append("education")

        if are_fields_complete_for_profile(education, EDUCATION_DETAIL_FIELDS):
            total += 3.34
        else:
            hints["detail"].append("education")
    else:
        hints["add"].append("education")



    ### Experience

    experience = ProfileExperience.objects.filter(profile=profile)
    if experience.exists():
        total += 20.0

        if are_fields_complete_for_profile(experience, EXPERIENCE_REQUIRED_FIELDS):
            total += 10.0
        else:
            hints["error"].append("experience")

        if are_fields_complete_for_profile(experience, EXPERIENCE_DETAIL_FIELDS):
            total += 3.34
        else:
            hints["detail"].append("experience")
    else:
        hints["add"].append("experience")


    certifications = ProfileCertification.objects.filter(profile=profile)
    if certifications.exists():

        if not are_fields_complete_for_profile(certifications, CERTIFICATION_REQUIRED_FIELDS):
            total -= 10
            hints["error"].append("certification")

    hints["error"] = {key: True for key in hints["error"]}
    hints["detail"] = {key: True for key in hints["detail"]}
    hints["add"] = {key: True for key in hints["add"]}

    return {
        "metric": min(int(total), 100),
        "hints": hints
    }


def are_fields_complete_for_profile(objects, fields):
    return all(getattr(row, field, None) for row in objects for field in fields)

