import React from 'react';
import { render } from 'react-dom';
import PubSub from 'pubsub-js';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import Candidate from './candidate';
import CandidateUtil from './candidate_util';
import SearchBar from './icims_search_bar.jsx';
import Networking from './networking';
import Pagination from './pagination';
import EmployerBulkControls from './employer_bulk_controls';
import { runTour } from './tour';

let jobDetailTour = [
    {
        intro: "This is the job detail page! This page shows you information about this job and about the candidates whom you are considering for the job.",
        position: 'center'
    },
    {
        element: "#react",
        intro: "This section shows you the candidates whom you have contacted.",
        position: 'top',
        tooltipClass: 'introjs-job-detail-tour-step-2'
    },
    {
        element: "#search_button",
        intro: 'To find more candidates, click here.'
    },
    {
        element: "select.list-filter-dropdown",
        intro: "You can filter candidates based on several criteria: whether they have responded to or accepted your requests, as well as their current candidate status in Bakround."
    },
    {
        element: "select.list-filter-dropdown",
        intro: "By default, the highest-scoring candidates are shown first. You can change the ordering here."
    },
    {
        element: '#show_tour',
        intro: "You can click this button to see this tour again.",
        position: 'bottom-right-aligned'
    }
];

let startTour = () => runTour(jobDetailTour, 'jobdetail');

class EmployerJobApp extends React.Component {
    constructor(props) {
        super(props);
        let data = JSON.parse(window.props);

        this.state = {
            candidates: [],
            total_candidates: 0,
            count_interested: 0,
            loading: false,

            filterBy: 'All',
            sortBy: 'contact_date_for_ordering',
            page_number: 0,
            per_page: 20,

            job_id: data.icims_job_id,
            job_open: data.job_open,
            tourDismissed: data.tour_dismissed,

            modal_callback: false,
            current_modal: null
        };

        this.changeFilterBy = this.changeFilterBy.bind(this);
        this.changeSortBy = this.changeSortBy.bind(this);
        this.getCandidates = this.getCandidates.bind(this);
        this.pageClicked = this.pageClicked.bind(this);
    }

    componentDidMount() {
        let _this = this;
        this.getCandidates().then(() => {
            if (!_this.state.tourDismissed) {
                Tours.startJobDetailTour();
            }
        });
    }

    changeFilterBy(event) {
        var _this = this;
        this.setState({filterBy: event.target.value, page_number: 0}, () => _this.getCandidates());
    }

    changeSortBy(event) {
        var _this = this;
        this.setState({sortBy: event.target.value, page_number: 0}, () => _this.getCandidates());
    }

    getCandidates(callback = null) {
        let per_page = this.state.per_page;

        let query = {
            page: this.state.page_number,
            per_page: this.state.per_page,
            ordering: this.state.sortBy
        };

        if (this.state.filterBy === 'Contacted') {
            query.contacted = true;
            query.responded = false;
        } else if (this.state.filterBy === 'Not Contacted') {
            query.contacted = false;
        } else if (this.state.filterBy === 'Responded') {
            query.responded = true;
        } else if (this.state.filterBy === 'Accepted') {
            query.accepted = true;
        } else if (this.state.filterBy === 'Declined') {
            query.responded = true;
            query.accepted = false;
        }
        let icims_job_id = this.state.job_id;

    	let _this = this;
        this.setState({loading: true});
        return Networking.json("POST", `/icims/job/${icims_job_id}/candidates_list`, query)
                  .then(response => {
            _this.setState({
                candidates: response.results.profiles,
                total_candidates: response.count,
                loading: false,
                count_interested: response.count_interested
            });

            if (callback) {
                callback();
            }
        });
    }

    pageClicked(value) {
    	if (value === 'Next') {
            let _this = this;
            this.setState({page_number: this.state.page_number + 1}, () => {
            	_this.getCandidates();
            	_this.selectAllCandidates(false);
            });

            $("#contact_selected_candidates_link").addClass('grayed-out-link');
    	} else if (value === 'Previous') {
            let _this = this;
            this.setState({page_number: this.state.page_number - 1}, () => {
            	_this.getCandidates();
            	_this.selectAllCandidates(false);
            });
    	}
    }

    render() {
        let candidatesBody = null;
        if (this.state.loading) {
            candidatesBody = (
                <div style={{textAlign: 'center'}}>
                  <i className='fa fa-2x fa-spinner fa-spin' />
                </div>
            );
        } else if (this.state.candidates && this.state.candidates.length > 0) {
            candidatesBody = <div>{this.state.candidates.map((candidate, i) =>
                <Candidate
                  key={candidate.id}
                  {...candidate}
                  showCandidateStatus
                  showRestrictLink
                  icims_job_id={this.state.job_id}
                  job_id={this.state.job_id}
                  candidate_ranking={1 + i + (this.state.page_number - 1) * this.state.page_size}
                  />)}</div>;
        } else {
            candidatesBody = (
                <div className='display-flex justify-content-center align-items-center' style={{height: '70vh'}}>
                    No Candidates.
                </div>
            );
        }
        return (
            <MuiThemeProvider>
                <div>
                    <div style={{display: 'flex', alignItems: "center", justifyContent: 'space-between', width: "100%"}}>
                        <h5 style={{ fontSize: 36, marginBottom: 10, display: "flex", alignItems: "center" }}>
                            <span>Current Candidates</span>
                            <a style={{fontSize: "24px", cursor: "pointer", fontSize: "75%", lineHeight: 0, position: "relative",  verticalAlign: "baseline", top: "-0.5em" }}
                               id="show_tour"
                               className="fa fa-question-circle-o"
                               title="show tour"
                               onClick={startTour} />
                            {this.state.job_open &&
                            <div style={{marginLeft: "15px" }}>
                                <a className="waves-effect waves-light btn btn-primary"
                                   href={`/icims/search/${this.state.job_id}`}
                                   id="search_button">Search for More...</a>
                            </div>}
                        </h5>
                        <a id="export_candidates_link"
                           className={this.state.count_interested > 0 ? "" : "grayed-out-link"}
                           style={{ fontWeight: "bold", marginLeft: 15 }}
                           href={`/icims/csv_export/${this.state.job_id}`}>Export Interested Candidates</a>
                    </div>
        	    <div className="filter-sort-controls">
                        <span>
                            <span>Sort by: </span>
                            <select className='list-filter-dropdown' ref="sortBySelect" onChange={this.changeSortBy} value={this.state.sortBy}>
                                <option value='score'>bScore</option>
                                <option value='distance'>distance</option>
                                <option value='total_experience_months'>experience</option>
                                <option value='last_updated_date'>last updated date</option>
                                <option value='contact_date_for_ordering'>contact date</option>
                                <option value='response_date_for_ordering'>response date</option>
                            </select>
                        </span>
                        <span>
        		    <span>Filter by: </span>
                    	    <select className='list-filter-dropdown' ref="filterBySelect" onChange={this.changeFilterBy} value={this.state.filterBy}>
                                <option value='All'>All</option>
                                <option value='Contacted'>Contacted</option>
                                <option value='Not Contacted'>Not Contacted</option>
                                <option value='Responded'>Responded</option>
                                <option value='Accepted'>Accepted</option>
                                <option value='Declined'>Declined</option>
                    	    </select>
                        </span>
        	    </div>
                    {!this.state.loading &&
                     <div style={{ display: 'flex', justifyContent: 'space-between', flexFlow: 'row wrap', alignItems: 'center', width: "100%"}}>
                         <EmployerBulkControls />
                         <div style={{marginLeft: "auto"}} />
                         <Pagination
                             countItems={this.state.total_candidates}
                             firstItem={(this.state.page_number * this.state.per_page) + 1}
                             lastItem={(this.state.page_number * this.state.per_page) + this.state.candidates.length}
                             pageClicked={this.pageClicked} />
                     </div>}
                    {candidatesBody}

                    {!this.state.loading &&
                     <div style={{ display: 'flex', justifyContent: 'space-between', flexFlow: 'row wrap', alignItems: 'center', width: "100%"}}>
                         <EmployerBulkControls />
                         <div style={{marginLeft: "auto"}} />
                         <Pagination
                             countItems={this.state.total_candidates}
                             firstItem={(this.state.page_number * this.state.per_page) + 1}
                             lastItem={(this.state.page_number * this.state.per_page) + this.state.candidates.length}
                             pageClicked={this.pageClicked}
                             jumpToTop/>
                     </div>}
        	</div>
            </MuiThemeProvider>
        );
    }
}

render(
    <EmployerJobApp {...JSON.parse(window.props)}/>,
    window.react_mount,
);
