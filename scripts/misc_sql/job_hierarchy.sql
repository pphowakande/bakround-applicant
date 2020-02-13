-- tplick, 11 August 2017
-- saving this here so I don't forget it

with recursive job_pairing as (
    (select distinct id as ancestor_job_id, id as descendant_job_id, 0 as recursion_level
     from job)
    union
    (select distinct job_pairing.ancestor_job_id, job.id, job_pairing.recursion_level + 1
     from job_pairing inner join job on (job.parent_job_id = job_pairing.descendant_job_id)
     where job_pairing.recursion_level < 3)
)
select distinct *
from job_pairing
order by ancestor_job_id, descendant_job_id, recursion_level
