-- Updated profile counts (5/18/17)

-- 1350 profiles
select distinct p.id
from profile p
    inner join profile_experience pe on p.id = pe.profile_id
where p.job_id = 1
    and p.user_id is NULL
    and (pe.position_title ilike '%med/surg%'
        or pe.position_title ilike '%med-surg%'
        or pe.position_title ilike '%medical-surgical%'
        or pe.position_title ilike '%medical/surgical%')
