-- Updated profile counts (5/18/17)

-- 2024 profiles
select distinct p.id
from profile p
    join profile_experience pe on pe.profile_id = p.id
where p.job_id = 1
    and p.user_id is NULL
    and pe.position_title ilike '%Nurse Practitioner%'
    and pe.position_title not ilike '%Student%'
