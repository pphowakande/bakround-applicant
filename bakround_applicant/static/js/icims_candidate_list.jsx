import React from 'react';
import Candidate from './icims_candidate.jsx';

const CandidateList = ({ loading, candidates, page_number, page_size,
                         icims_job_id, job_id, mode, show_restrict_link,
                         showCandidateStatus, refreshCandidates }) => {
    if (loading) {
        return (
          <div style={{textAlign: 'center'}}>
            <i className='fa fa-2x fa-spinner fa-spin' />
          </div>
        );
    }

    if (candidates && candidates.length > 0) {
        let commonProps = {
            icims_job_id, job_id,
            mode, show_restrict_link, showCandidateStatus,
            refreshCandidates
        };
        return <div>{candidates.map((candidate, i) =>
            <Candidate
                key={candidate.id}
                candidate_ranking={1 + i + page_number * page_size}
                {...commonProps}
                {...candidate}
              />)}</div>;
    }

    return <div className='display-flex justify-content-center align-items-center' style={{height: '70vh'}}>Modify your filters to get searching for candidates!</div>;
};

export default CandidateList;
