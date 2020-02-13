-- Updated profile counts (5/18/17)

-- 942 profiles
select distinct p.id
from profile p
    inner join profile_experience pe on p.id = pe.profile_id
where p.job_id = 1
    and p.user_id is NULL
    and (pe.position_title ilike '%operating%room%'
        or pe.position_title ilike '% OR nurse%'
        or pe.position_title ilike '% OR RN%'
        or pe.position_title ilike '%scrub%'
        or pe.position_title ilike '%circulating%'
        or pe.position_title ilike '%first%assistant%')

-- 205 profiles
select distinct p.id
from profile_certification pc
    join profile p on pc.profile_id = p.id
where p.job_id = 1
    and p.user_id is NULL
    and pc.certification_name ilike '%cnor%'
