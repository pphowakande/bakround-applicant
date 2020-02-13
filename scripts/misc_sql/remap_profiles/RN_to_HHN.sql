-- Updated profile counts (5/18/17)

-- 179 profiles
select id
FROM profile
WHERE job_id = 1
    AND user_id is NULL
    AND (summary ILIKE '%home health%'
        OR summary ILIKE '%Home Health%'
        OR summary ILIKE '%Home Care%'
        OR summary ILIKE '%home care%'
        OR summary ILIKE '%homecare%'
        OR summary ILIKE '%HHA%')

-- 1192 profiles
select distinct p.id
from profile p
    join profile_skill ps ON ps.profile_id = p.id
where p.job_id = 1
    AND user_id is NULL
    AND (ps.skill_name ILIKE '%ASSISTED LIVING HOME%'
        OR ps.skill_name ILIKE '%HHA%'
        OR ps.skill_name ILIKE '%HHA CERTIFIED%'
        OR ps.skill_name ILIKE '%HOME HEALTH AIDE%'
        OR ps.skill_name ILIKE '%CERTIFIED HOME HEALTH%'
        OR ps.skill_name ILIKE '%ASSISTED LIVING%'
        OR ps.skill_name ILIKE '%ASSISTED LIVING FACILITIES%')

-- 1168 profiles
select distinct p.id
from profile p
    join profile_experience pe ON pe.profile_id = p.id
where p.job_id = 1
    AND user_id is NULL
    AND (pe.position_title ILIKE '%ASSISTED LIVING HOME%'
	    OR pe.position_title ILIKE '%HHA%'
	    OR pe.position_title ILIKE '%HHA CERTIFIED%'
	    OR pe.position_title ILIKE '%HOME HEALTH AIDE%'
	    OR pe.position_title ILIKE '%CERTIFIED HOME HEALTH%'
	    OR pe.position_title ILIKE '%ASSISTED LIVING%'
	    OR pe.position_title ILIKE '%ASSISTED LIVING FACILITIES%'
	    OR pe.position_title ILIKE '%Homecare%'
	    OR pe.position_title ILIKE '%Home Care%'
	    OR pe.position_title ILIKE '%home%')

-- 1999 profiles
select distinct p.id
from profile p
    join profile_experience pe ON pe.profile_id = p.id
where p.job_id = 1
    AND user_id is NULL
    AND (pe.position_description ILIKE '%ASSISTED LIVING HOME%'
        OR pe.position_description ILIKE '%HHA%'
        OR pe.position_description ILIKE '%HHA CERTIFIED%'
        OR pe.position_description ILIKE '%HOME HEALTH AIDE%'
        OR pe.position_description ILIKE '%CERTIFIED HOME HEALTH%'
        OR pe.position_description ILIKE '%ASSISTED LIVING%'
        OR pe.position_description ILIKE '%ASSISTED LIVING FACILITIES%'
        OR pe.position_description ILIKE '%Homecare%'
        OR pe.position_description ILIKE '%Home Care%')

-- 567 profiles
select distinct p.id
from profile p
    join profile_certification pc ON pc.profile_id = p.id
where p.job_id = 1
    AND user_id is NULL
    AND (pc.certification_name ILIKE '%ASSISTED LIVING HOME%'
        OR pc.certification_name ILIKE '%HHA%'
        OR pc.certification_name ILIKE '%HHA CERTIFIED%'
        OR pc.certification_name ILIKE '%HOME HEALTH AIDE%'
        OR pc.certification_name ILIKE '%CERTIFIED HOME HEALTH%'
        OR pc.certification_name ILIKE '%ASSISTED LIVING%'
        OR pc.certification_name ILIKE '%ASSISTED LIVING FACILITIES%')
