import React from 'react';
import { render } from 'react-dom';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import CandidateList from './candidate_list.jsx';
import Candidate from './candidate.jsx';
import SearchBar from './search_bar.jsx';
import Networking from './networking';
import Pagination from './pagination';
import EmployerBulkControls from './employer_bulk_controls';
import { runTour } from './tour';

const searchTourSteps = [
    {
        intro: "This is the search page! You can find new candidates here.",
        position: 'center'
    },
    {
        element: ".filter-bar",
        intro: "You can filter candidates based on these criteria."
    },
    {
        element: "#advanced_search_link",
        tooltipClass: 'introjs-advanced-search-step',
        position: 'top',
        intro: 'Advanced Search allows you to specify exact search terms that must appear ' +
            '(or must not appear) in the candidates\' profiles that are presented to you.  ' +
            'Clicking this link will show the Advanced Search window.  To see only those profiles ' +
            'containing a particular set of terms, enter those terms in the field ' +
            'labeled "All of these words."  To exclude profiles containing any term out of ' +
            'a particular set of terms, enter those terms in the field labeled "None of these words."',
    },
    {
        element: "#score_scale_image",
        intro: "Each candidate has been assigned a bScore that indicates how good a fit they are for this job.  " +
               "Candidates are scored according to this scale.  bScores range from 300 (Minimal Fit) to 850 (Best Fit)."
    },
    {
        element: "select.list-filter-dropdown",
        intro: "By default, the highest-scoring candidates are shown first.  You can change the ordering here."
    },
    {
        element: ".applicant-card",
        intro: "Each candidate shows up as a card in this list."
    },
    {
        element: ".send-intro-button",
        intro: "Click this button to email an introductory message to the candidate."
    },
    {
        element: ".loading-details-icon .fa-angle-down",
        intro: "To view more detailed information about the candidate, click this arrow."
    },
    {
        element: ".feedback-link-or-score-line",
        intro: "After viewing a candidate's profile, you can give us feedback on the candidate's bScore " +
               "by clicking here.  After you give feedback on a candidate, this line will show the score " +
               "that you gave for that candidate.  Your feedback will be used to help us improve the accuracy " +
               "of bScores.",
    },
    {
        element: ".bulk-controls",
        intro: 'To contact multiple candidates at once, click "Select All," then click "Send Intro."'
    },
    {
        element: '#show_tour',
        intro: "You can click this button to see this tour again.",
        position: 'bottom-right-aligned'
    }
];

let startTour = () => runTour(searchTourSteps, "search");

class EmployerSearchApp extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            candidates: [],
            num_results: 0,
            page_number: 1,
            page_size: 20,
            ordering: 'score',
            loading: false,
            filters: [
                {key: 'job_id', value: this.props.job_profile.id, copy: this.props.job_profile.job_name},
                {key: 'location', value: this.props.city + ', ' + this.props.state},
                {key: 'distance', value: 50, copy: 'less than 50 miles'}
            ],

            job_id: this.props.job_id,
            modal_callback: false,
            current_modal: null
        };

        this.getCandidates = this.getCandidates.bind(this);
        this.pageClicked = this.pageClicked.bind(this);
        this.orderingChanged = this.orderingChanged.bind(this);
        this.pageSizeChanged = this.pageSizeChanged.bind(this);
        this.filtersChanged = this.filtersChanged.bind(this);
    }

    componentDidMount() {
        this.getCandidates();
        if (!this.props.tour_dismissed) {
            startTour();
        }
    }

    pageClicked(value, jump) {
        if (value === 'Next') {
            this.setState({page_number: this.state.page_number+1}, function() {
                this.getCandidates();
            });
        } else if (value === 'Previous') {
            this.setState({page_number: this.state.page_number-1}, function() {
                this.getCandidates();
            });
        }
    }

    orderingChanged(ordering) {
        let _this = this;
        this.setState({ordering: ordering, page_number: 1}, () => _this.getCandidates());
    }

    pageSizeChanged(pageSize) {
        let _this = this;
        this.setState({page_size: pageSize, page_number: 1}, () => _this.getCandidates());
    }

    filtersChanged(filters) {
        let _this = this;
        this.setState({filters: filters, page_number: 1}, () => _this.getCandidates());
    }

    getCandidates() {
        let postData = {};

        let advanced_search_params = {"all": "", "any": "", "none": ""};
        let any_advanced_search_params = false;

        this.state.filters.map(function(filter, index) {
            if (filter.key === 'distance') {
                postData.distance = filter.value;
            } else if (filter.key === 'location') {
                postData.city = filter.value.split(',')[0].trim();
                postData.state = filter.value.split(',')[1].trim();
            } else if (filter.key.indexOf("advanced_") === 0) {
                let filter_type = filter.key.slice(9);
                advanced_search_params[filter_type] = filter.value;
                any_advanced_search_params = true;
            } else {
                postData[filter.key] = filter.value;
            }
        });

        if (any_advanced_search_params) {
            postData.advanced = advanced_search_params;
        }

        postData.ordering = this.state.ordering;
        postData.page = this.state.page_number;
        postData.employer_job_id = this.state.job_id;
        postData.page_size = this.state.page_size;

        if (postData.job_id && postData.city && postData.state) {
            this.setState({loading: true});
            let _this = this;
            Networking.json("POST", "/profile/search", postData).catch(err => {
                console.error(_this.props.url, err.responseCode, err.toString());
                _this.setState({candidates: [], num_results:0});
            }).then(data =>
                this.setState({
                    candidates: data.profiles,
                    num_results: data.num_results,
                    page_number: data.page_number,
                    loading: false
                }));
        } else {
            this.setState({candidates: [], num_results:0});
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
                  showsSeenEye
                  employer_job_id={this.state.job_id}
                  job_id={this.state.job_id}
                  candidate_ranking={1 + i + (this.state.page_number - 1) * this.state.page_size}
                  />)}</div>;
        } else {
            candidatesBody = (
                <div className='display-flex justify-content-center align-items-center' style={{height: '70vh'}}>
                    No Results. Try broadening your search.
                </div>
            );
        }
        return (
          <MuiThemeProvider>
            <div>
              <h1 style={{fontSize: 36, marginBottom: 5}}>
                  <span>Candidate Search</span>
                  <a style={{fontSize: "24px", cursor: "pointer", fontSize: "75%", lineHeight: 0, position: "relative",  verticalAlign: "baseline", top: "-0.5em" }}
                      className="fa fa-question-circle-o"
                      title="show tour"
                      onClick={startTour} />
              </h1>

              <img src={window.scoring_scale_src}
                   style={{ maxWidth: 434, width: "100%" }}
                   id="score_scale_image" />
              <SearchBar
                  showAdvancedSearch={this.props.show_advanced_search}
                  orderingChanged={this.orderingChanged}
                  pageSizeChanged={this.pageSizeChanged}
                  filtersChanged={this.filtersChanged}
                  loading={this.state.loading}
                  filters={this.state.filters}
                  num_pages={this.state.num_pages}
                  page_number={this.state.page_number}
                  ordering={this.state.ordering}
                  page_size={this.state.page_size}
                  state_list={this.props.state_list}
                  includeSortBy='true'
              />
              {!this.state.loading &&
               <div style={{ display: 'flex', justifyContent: 'space-between', flexFlow: 'row wrap', alignItems: 'center', width: "100%"}}>
                   <EmployerBulkControls />
                   <div style={{marginLeft: "auto"}} />
                   <Pagination
                       countItems={this.state.num_results}
                       firstItem={(this.state.page_size * (this.state.page_number - 1)) + 1}
                       lastItem={(this.state.page_size * (this.state.page_number - 1)) + this.state.candidates.length}
                       pageClicked={this.pageClicked} />
               </div>}
              {candidatesBody}
              {!this.state.loading &&
               <div style={{ display: 'flex', justifyContent: 'space-between', flexFlow: 'row wrap', alignItems: 'center', width: "100%"}}>
                   <EmployerBulkControls />
                   <div style={{marginLeft: "auto"}} />
                   <Pagination
                       countItems={this.state.num_results}
                       firstItem={(this.state.page_size * (this.state.page_number - 1)) + 1}
                       lastItem={(this.state.page_size * (this.state.page_number - 1)) + this.state.candidates.length}
                       pageClicked={this.pageClicked}
                       jumpToTop />
               </div>}
            </div>
          </MuiThemeProvider>
        );
    }
}

render(
    <EmployerSearchApp {...JSON.parse(window.props)}/>,
    window.react_mount
);
