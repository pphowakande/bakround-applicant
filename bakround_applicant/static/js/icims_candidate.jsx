'use strict';

var React = require('react');
var ReactDOM = require('react-dom');
var PubSub = require('pubsub-js');
import Snackbar from 'material-ui/Snackbar';
import ReactTooltip from 'react-tooltip';
import confirmable from 'react-confirm';
import { createConfirmation } from 'react-confirm';
import Dialog from 'material-ui/Dialog';
import FlatButton from 'material-ui/FlatButton';
import confirm from './confirm';
import Checkbox from 'material-ui/Checkbox';
import Modal from 'react-modal';
import CandidateUtil from './candidate_util';
import Networking from './networking';

function formatDate(d, opts = { year: 'numeric', month: 'numeric', day: 'numeric' }) {
    return d.toLocaleDateString(navigator.languages ? navigator.languages[0] : navigator.language, opts);
}

export default class Candidate extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            visible: true,
            expanded: false,
            contacted: props.contacted,
            expanded_data: '', // JS quirk, silently fail when accessing properties
            loading_details: false,
            snackbarOpen:false,
            snackbarContent: '',
            checked: false,
            modalIsOpen: false,
            possibleStatuses: null,
            currentStatusText: this.props.candidate_status_text,
            showRestrictLink: props.show_restrict_link,
            feedbackModalIsOpen: false,
            hasFeedbackBeenSubmitted: props.feedback,
            sliderPosition: this.props.score,
            score: this.props.score ? Math.round(this.props.score) : null,
            previously_viewed: this.props.previously_viewed,

            loadingContactInfo: false,
            emails: [],
            phones: []
        };

        this.contactEventSubscriber = this.contactEventSubscriber.bind(this);
        this.checkedEventSubscriber = this.checkedEventSubscriber.bind(this);
        PubSub.subscribe('candidate.ui.checked', this.checkedEventSubscriber);
        PubSub.subscribe('candidate.action.contact', this.contactEventSubscriber);

        this.clickedContactApplicant = this.clickedContactApplicant.bind(this);
        this.openModal = this.openModal.bind(this);
        this.afterOpenModal = this.afterOpenModal.bind(this);
        this.closeModal = this.closeModal.bind(this);
        this.submitStatusForm = this.submitStatusForm.bind(this);

        this.openFeedbackModal = this.openFeedbackModal.bind(this);
        this.afterOpenFeedbackModal = this.afterOpenFeedbackModal.bind(this);
        this.closeFeedbackModal = this.closeFeedbackModal.bind(this);
        this.submitFeedback = this.submitFeedback.bind(this);
        this.restrictProfile = this.restrictProfile.bind(this);
        this.applicantCheckboxClicked = this.applicantCheckboxClicked.bind(this);

        this.changeSliderPosition = this.changeSliderPosition.bind(this);

        this.downloadProfileButtonClicked = this.downloadProfileButtonClicked.bind(this);
    }

    static setAllChecked(goal) {
        PubSub.publish('candidate.ui.checked', { checked: goal });
    }

    static contactChecked() {
        PubSub.publish('candidate.action.contact', { showInSnackbar: false });
    }

    openModal(e) {
        if (e) {
            e.stopPropagation();
        }

        this.setState({modalIsOpen: true});
        this.getCandidateStatusContent();
    }

    afterOpenModal() {}

    closeModal() {
        this.setState({modalIsOpen: false});
    }

    openFeedbackModal(e) {
        if (e) {
            e.stopPropagation();
        }

        if (!this.state.downloadProfileButtonClicked) {
            alert('Please view the candidate\'s extended profile (by clicking "Download Profile") before giving feedback.');
            this.showExpandedContent();
            return;
        }

        this.setState({feedbackModalIsOpen: true});
    }

    afterOpenFeedbackModal() {}

    closeFeedbackModal() {
        this.setState({feedbackModalIsOpen: false});
    }

    showExpandedContent() {
        if (!this.state.expanded_data) {
            let _this = this;
            this.setState({loading_details: true});
            Networking.json("GET", "/icims/profile_summary/" + this.props.id, {
                icims_job_id: this.props.job_id
            }).then(data => _this.setState({
                                expanded: true,
                                expanded_data: data,
                                loading_details: false,
                                previously_viewed: true
                            }));
        } else {
            this.setState({expanded: true, previously_viewed: true});
        }
    }

    hideExpandedContent() {
        this.setState({expanded: false});
    }

    contactEventSubscriber(msg, data) {
        if (data.profile_id && data.profile_id !== this.props.id) {
            return;
        }

        if (!this.state.checked) {
            return;
        }

        this.contactApplicant(data.showInSnackbar || false);
    }

    checkedEventSubscriber(msg, data) {
        if (data.profile_id && data.profile_id !== this.props.id) {
            return;
        }
        console.log("Checked event subscriber", msg, data);
        let different = data.checked !== this.state.checked;
        this.setState(st => ({...st, checked:data.checked}));
        if (different) {
            PubSub.publish(data.checked ? 'bulk_controls.increment' : 'bulk_controls.decrement', {});
        }
    }

    componentDidMount() {
        this.getContactInfo();
    }

    componentWillReceiveProps(nextProps) {
	this.setState({previously_viewed: nextProps.previously_viewed});
    }

    applicantCardClicked(i) {
        if (this.state.expanded) this.hideExpandedContent();
        else                     this.showExpandedContent();
    }

    applicantCheckboxClicked(event) {
        event.stopPropagation();
        this.setState({checked: !this.state.checked});
        PubSub.publish(!this.state.checked ? 'bulk_controls.increment' : 'bulk_controls.decrement', {});
    }

    contactApplicant(showInSnackbar) {
      	if (!this.state.contacted) {
            let _this = this;

            // TODO: error handling
            Networking.addToJob(_this.props.job_id, _this.props.id, true).then(data => {
                let newState = { contacted: true };

                if (showInSnackbar) {
                    let verbs = ["added"];

                    if (newState.contacted) {
                        verbs.push("contacted");
                    }

                    newState.snackbarOpen = true;
                    newState.snackbarContent = `Applicant has been ${verbs.join(' & ')}.`;
	        }
                _this.setState(newState);
            });
      	}
    }

    clickedContactApplicant(i) {
      	i.stopPropagation();
        this.contactApplicant(true);
    }

    getContactInfo() {
        if (this.props.accepted) {
            let _this = this;
            this.setState({ loadingContactInfo: true });
            Networking.getContactInfo(this.props.candidate_id).then(res =>
                _this.setState({ loadingContactInfo: false, emails: res.emails, phones: res.phones }));
        }
    }

    restrictProfile(event) {
        if (event) {
            event.stopPropagation();
        }

    	let _this = this;
        Networking.json("POST", "/icims/restrict_profile/" + this.props.id)
                  .then(data => _this.setState({restricted: true}));
    }

    handleRequestClose() {
        this.setState({snackbarOpen: false});
    }

    getCandidateStatusContent() {
        let _this = this;

        Networking.json("GET", "/icims/candidate_status/" + this.props.candidate_id)
                  .then(data => _this.setState({candidate_status: data}));

        Networking.json("GET", "/icims/fetch_possible_statuses")
                  .then(data => _this.setState({possibleStatuses: data}));

        Networking.json("GET", "/icims/fetch_possible_reject_reasons")
                  .then(data => _this.setState({possibleRejectReasons: data}));
    }

    submitStatusForm() {
        let new_status = $("select[name='new_status']").val();
        if (new_status) new_status = parseInt(new_status);
        let reject_reason = $("select[name='reject_reason']").val();
        if (reject_reason) reject_reason = parseInt(reject_reason);

        if (new_status == 0) {
            return;
        }

        let new_status_text = "New Candidate"; //$("select[name='new_status'] option:selected").text();

        for (let x of this.state.possibleStatuses) {
            if (x.id === new_status) {
                new_status_text = x.status;
                break;
            }
        }

        let new_status_notes = $("#new_status_notes").val();

        this.setState({currentStatusText: new_status_text});

        let _this = this;
        Networking.json("POST", "/icims/change_candidate_status/" + this.props.candidate_id, {
            new_status: new_status,
            new_status_notes: new_status_notes,
            reject_reason: reject_reason
        }).then(data => _this.closeModal());
    }

    submitFeedback() {
        let params = {};
        params.profile_id = this.props.id;
        params.icims_job_id = this.props.job_id;

        let form = $(".score_feedback_form");

        form.find('input').each(function (i, elt){
            let name = $(elt).attr("name");

            if (name && name.indexOf("column_") == 0){
                params[name] = $(elt).is(":checked") ? "1" : "";
            }
        });

        if (form.find("#should_interview_yes").is(":checked")){
            params.should_interview = "1";
        }

        if (form.find("#should_interview_no").is(":checked")){
            params.should_not_interview = "1";
        }

        params.comment = form.find("textarea[name='comment']").val();
        params.bscore_value = this.state.sliderPosition;

        if (!this.validateScoreFeedbackParameters(params)) {
            return;
        }

        params.saved_search_id = this.props.saved_search_id;
        params.candidate_ranking = this.props.candidate_ranking;
        params.actual_bscore = this.state.score;

        Networking.json("POST", "/icims/submit_feedback_post", params);

        this.closeFeedbackModal();
        this.setState({hasFeedbackBeenSubmitted: params.bscore_value});
    }

    changeSliderPosition(newPosition) {
        this.setState({sliderPosition: newPosition.x});
    }

    validateScoreFeedbackParameters(params) {
        if (params.comment.length < 30){
            alert("Please provide a longer comment.");
            return false;
        }

        if (!params.should_interview && !params.should_not_interview) {
            alert("Please answer the question about interviewing the candidate.");
            return false;
        }

        return true;
    }

    downloadProfileButtonClicked(e) {
        e.stopPropagation();
        this.setState({
            downloadProfileButtonClicked: true,
            previously_viewed: true
        });
    }

    render() {
        if (!this.state.visible) {
            return <div />; // TODO: what about null?
        }

      	let contact_item = null;
      	let experience_items = null;
      	if (this.props.sourced_by_employer) {
      		contact_item = <span className='contactIcon matched-pill'> Applied </span>;
      	} else if (this.props.responded && !this.props.accepted) {
      		contact_item = <span className='contactIcon matched-pill pill-declined'> Declined </span>;
      	} else if (this.props.accepted) {
      		contact_item = <span className='contactIcon matched-pill pill-accepted'> Accepted </span>;
      	} else if (this.state.contacted) {
      		contact_item = <span className='contactIcon contacted-pill'> Contacted </span>;
      	} else {
      		contact_item = <span onClick={this.clickedContactApplicant} className='btn-primary pull-right send-intro-button' data-place='right' data-delay-show='500' data-tip="Add this candidate, and contact them via email expressing interest"> Send intro
      		</span>;
      	}

        let experienceContent = null;
    	var experience_array = this.state.expanded_data.experience || [];
    	var total_experience_years = Math.floor(this.props.total_experience_months/12);

    	if (experience_array.length > 0) {
    	    experience_items = experience_array.map((experience, index) =>
                <div key={index} style={{padding: '0 0 7px 0'}} className='experience-item'>
    	            {experience.company_name && <div>{experience.company_name}</div>}
    	            <div>{experience.position_title} {experience.date_range}</div>
    	        </div>);
    	}

    	if (total_experience_years >= 1) {
            let capped_experience_years = total_experience_years >= 20 ? "20+" : total_experience_years;
            experienceContent = (
                <div className='candidateExperienceContainer line'>
                    <div className='candidateLabel'>EXPERIENCE</div>
                    <div className='candidateContent'>
                    <div>({capped_experience_years} year{total_experience_years != 1 ? "s" : ""} in total)</div>
                        {this.state.expanded && <div>{experience_items}</div>}
                    </div>
                </div>
            );
    	} else if (this.state.expanded && experience_array.length > 0) {
            experienceContent = (
                <div className='candidateExperienceContainer line'>
                    <div className='candidateLabel'>EXPERIENCE</div>
                    <div className='candidateContent'>
                        {experience_items}
                    </div>
                </div>
            );
    	}

    	let expander_icon = null;
    	if (this.state.loading_details) {
    	    expander_icon = <div className='loading-details-icon'><i className='fa fa-2x fa-spinner fa-spin' /></div>;
    	} else if (!this.state.expanded) {
    	    expander_icon = <div className='loading-details-icon'><i className='fa fa-2x fa-angle-down' /></div>;
    	} else {
    	    expander_icon = <div className='loading-details-icon'><i className='fa fa-2x fa-angle-up' /></div>;
        }

        let educationContent = null;
    	if (this.state.expanded) {
    	    var download_profile_button = null;
    	    var education_array = this.state.expanded_data.education || [];
    	    if (education_array.length > 0) {
                educationContent = <div className='candidateEducationContainer line'>
                    <div className='candidateLabel'>EDUCATION</div>
                        <div className='candidateContent'>
                        {education_array.map((ed, index) =>
                            <div className='candidateEducation' key={index}>
                              {ed.degree_year && `${ed.degree_year} - `}{ed.school_name}{ed.degree_name && ` (${ed.degree_name})`}
                            </div>
                        )}
                    </div>
                </div>;
    	    }
    	    download_profile_button = (
                <div style={{'textAlign':'right', 'margin': '5px 0px'}}>
    	            <a target='_blank'
    	               href={'/profile/pdf/icims/' + this.props.id + '?hide_bscore=t&ejid=' + this.props.job_id}
    	               className='btn-primary send-intro-button'
    	               onClick={this.downloadProfileButtonClicked}
    	               >&nbsp;Download profile</a>
                    <a target='_blank'
                       href={`/icims/preview_intro/${this.props.job_id}?profile_id=${this.props.id}`}
                       className='btn-primary send-intro-button'
                       >&nbsp;Preview Intro</a>
    	        </div>
            );
    	}

        let certificateContent = null;
        let cs = this.state.expanded_data.certifications || [];
        if (this.state.expanded && cs.length > 0) {
            certificateContent = <div className='candidateCertificationContainer line'>
                    <div className='candidateLabel'>CERTIFICATIONS</div>
                        <div className='candidateContent'>
                        {cs.map((c, index) =>
                            <div className='candidateCertification' key={index}>{c.name} (issued {c.issued_year})</div>
                        )}
                    </div>
                </div>;
        }

        let skillsContent = null;
        let skills = this.state.expanded_data.skills || [];
        if (this.state.expanded && skills.length > 0) {
            skillsContent = <div className='candidateSkillsContainer line'>
                    <div className='candidateLabel'>SKILLS</div>
                        <div className='candidateContent'>
                        {skills.map((s, index) =>
                            <div className='candidateCertification' key={index}>{s.name}</div>
                        )}
                    </div>
            </div>;
        }

        let statusName = "New Candidate";
        if (this.state.currentStatusText) {
            statusName = this.state.currentStatusText;
        }

    	let recently_updated = false;
        let last_updated = null;
    	if (this.props.last_updated_date) {
                let lastUpdated = new Date(this.props.last_updated_date);
                let days_past = ((new Date()).getTime() - lastUpdated.getTime()) / (1000 * 3600 * 24);

                if (days_past <= 30) {
                    recently_updated = true;
                }

                last_updated = lastUpdated.toLocaleDateString(navigator.languages ? navigator.languages[0] : navigator.language);
    	}

        const actions = [
          <FlatButton
            label="Cancel"
            primary={true}
            onTouchTap={(i) => this.handleClose(i)}
          />,
          <FlatButton
            label="Yes"
            primary={true}
            onTouchTap={(i) => this.handleConfirm(i)}
          />,
        ];

        let modal = CandidateUtil.make_status_modal.bind(this)();

        // ReactTooltip.rebuild()

    	return (
            <div className='applicant-card' onClick={(i) => this.applicantCardClicked(i)}>
                <ReactTooltip />
                <div className='action-top-bar'style={{ display: 'flex', alignItems: "center" }}>
                    <Checkbox
                        checked={this.state.checked}
                        key={this.props.id}
                        data-pid={this.props.id}
                        className="candidate-checkbox"
                        style={{width: 'inherit', height: 'inherit', marginRight: "-5.5px"}}
                        onClick={this.applicantCheckboxClicked}
                    />
                    {contact_item}

	            <span style={{ marginLeft: "auto" }}/>

                    {this.state.previously_viewed && this.props.showsSeenEye &&
                     <i className="fa fa-eye" style={{ margin: "0 10px", fontSize: "24px", display: "flex", alignItems: "center"}}
                        title="You have viewed this profile." />}
                    {this.props.showCandidateStatus &&
                     <span className='candidate-status' style={{ margin: "0px 10px", justifySelf: 'flex-end'}}>
                         <span className='hidden-xs'>
                             <a href="#!" style={{ 'fontWeight': 'bold' }} onClick={(e) => this.openModal(e)}
                                 >{statusName}</a>
                         </span>
                     </span>}
                    {last_updated &&
                     <span className='last-updated-date' style={{justifySelf: 'flex-end',
                                                                 margin: "0 10px",
                                                                 backgroundColor: recently_updated ? 'rgb(255, 255, 99)' : 'inherit'}}>
                         <span className='hidden-xs'>Last</span> updated <b>{last_updated}</b>
                     </span>
                    }
                </div>
                <div style={{display: "flex", flexDirection: "row" }}>
                    <div className='candidate-info-container line'>
                        <div style={{ display: 'flex', flexDirection: 'row' }}>
                            <div className='candidateScore' style={{color: CandidateUtil.colorCodeScore(this.state.score), display: 'flex', flexDirection: 'column'}}>
                                {this.state.score || ''}
                                {this.state.hasFeedbackBeenSubmitted
                                   ? <span style={{fontSize: '12px', color: 'black'}}
                                           className="feedback-link-or-score-line">
                                         You said: {this.state.hasFeedbackBeenSubmitted}
                                     </span>
                                   : <a href="#!" onClick={this.openFeedbackModal} style={{fontSize: '12px'}}
                                        className="feedback-link-or-score-line">Feedback</a>
                                }
                            </div>
                            <div className='candidateTitle candidateContent'
                                 style={{ display: 'flex', alignItems: 'center', paddingBottom: "3px" }}
                                 data-place='right'
                                 data-delay-show='700'
                                 data-tip="Once you contact the candidate and they respond, you'll be able to see their full name and contact info">{this.props.first_name + ' ' + this.props.last_name}</div>
                        </div>
                        <div className='candidateLocationContainer line'>
                            <span className='candidateLabel'>LOCATION</span>
                            <div className='candidateLocation candidateContent'>{this.props.city}, {this.props.state} ({Math.floor(this.props.distance)} miles away)</div>
                        </div>
                        {this.props.accepted &&
                        <div className="candidate-contact-info-container line" style={{ width: "50%" }}>
                            {this.state.loadingContactInfo &&
                             <div style={{textAlign: 'center'}}>
                                 <i className='fa fa-2x fa-spinner fa-spin' />
                             </div>}
                            {!this.state.loadingContactInfo && <div className="emails line">
                                <span className='candidateLabel'>EMAIL</span>
                                <div className="emailsList candidateContent">
                                    {this.state.emails.map(({ value, assurance }, index) =>
                                        <div className='candidateEmailAddress' key={index}>{value}</div>
                                    )}
                                </div>
                            </div>}
                            {!this.state.loadingContactInfo && <div className="phones line">
                                <span className='candidateLabel'>PHONE</span>
                                <div className="phonesList candidateContent">
                                    {this.state.phones.map(({ value, assurance }, index) =>
                                        <div className='candidatePhoneNumber' key={index}>{value}</div>
                                    )}
                                </div>
                            </div>}
                        </div>}
                        {experienceContent}
                        {educationContent}
                        {certificateContent}
                        {skillsContent}
                    </div>
                </div>
                {download_profile_button}
                {this.state.showRestrictLink && this.props.accepted &&
                    (this.state.restricted
                        ? <span style={{lineHeight: '40px'}}>(Restricted)</span>
                        : <a style={{lineHeight: '40px', fontWeight: 'bold'}} href="#!" onClick={this.restrictProfile}>Restrict This Profile</a>)}
                {expander_icon}
                <Snackbar
                  open={this.state.snackbarOpen}
                  message={this.state.snackbarContent}
                  autoHideDuration={3000}
                  onRequestClose={this.handleRequestClose.bind(this)}
                  style={{textAlign:'center'}}
                />
                {modal}
                {CandidateUtil.make_feedback_modal.bind(this)()}
            </div>
        );
    }
}

Candidate.defaultProps = {
    showCandidateStatus: false,
    showRestrictLink: false,
    showSeenEye: false
};
