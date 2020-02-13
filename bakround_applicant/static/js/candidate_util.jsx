'use strict';
var React = require('react');
import Modal from 'react-modal';
import InputSlider from 'react-input-slider';

const modalStyles = {
    content : {
      top                   : '50%',
      left                  : '50%',
      right                 : 'auto',
      bottom                : 'auto',
      marginRight           : '-50%',
      transform             : 'translate(-50%, -50%)',
      textAlign             : 'center',
      maxWidth              : '500px'
    },
    overlay                 : {zIndex: 1001}
};

export default class CandidateUtil {
    static make_bad_resume_options() {
        return [
            {
                "name": "column_wrong_job",
                "text": "Application does not make sense for this position"
            },
            {
                "name": "column_wrong_language",
                "text": "Non-English resume"
            },
            {
                "name": "column_incomplete",
                "text": "Incomplete resume"
            },
            {
                "name": "column_insuff_exp",
                "text": "Insufficient work experience"
            },
            {
                "name": "column_insuff_skills",
                "text": "Insufficient skills"
            },
            {
                "name": "column_insuff_certs",
                "text": "Insufficient certification(s)"
            },
            {
                "name": "column_unknown_employers",
                "text": "Unrecognized previous employer(s)"
            },
            {
                "name": "column_unknown_schools",
                "text": "Unrecognized school(s)"
            }
        ];
    }

    static colorCodeScore(bScore) {
        let score_ranges = [
            {label: 'very poor', min: 300, max: 410, color:'#e63c2f'},
            {label: 'poor', min: 410, max: 520, color:'#ff9e16'},
            {label: 'fair', min: 520, max: 630, color:'#00e000'},
            {label: 'good', min: 630, max: 740, color:'#8ad2e6'},
            {label: 'excellent', min: 740, max: 851, color: '#2020d0'}
	];
        let matching_score = score_ranges.filter(score_range => {
            if (bScore >= score_range.min && bScore <= score_range.max) {
                return score_range;
            }
            return undefined;
        })[0];
        return matching_score ? matching_score.color : '';
    }

    static make_modal(name, modal_content, options) {
        /* call .bind(this) from EmployerApp before invoking */

        let _this = this;
        return (
            <Modal
              isOpen={this.state && this.state.current_modal == name}
              style={modalStyles}
              contentLabel="Modal">
                {modal_content}
                <div>
                    {options.map(text =>
                     <input type="button" value={text}
                            onClick={e => _this.resolve_modal(text)}
                            style={{margin: '20px'}} />)}
                </div>
            </Modal>
        );
    }

    static make_feedback_modal() {
        /* call .bind(this) from Candidate before invoking */

  	const modalStyles = {
            content : {
              top        : '50%',
              left       : '50%',
              right      : 'auto',
              bottom     : 'auto',
              marginRight: '-50%',
              transform  : 'translate(-50%, -50%)',
              textAlign  : 'center'
            },
            overlay      : {zIndex: 1001}
        };

        let options = CandidateUtil.make_bad_resume_options();

  	return (
            <Modal
                isOpen={this.state.feedbackModalIsOpen}
                onAfterOpen={this.afterOpenFeedbackModal}
                onRequestClose={this.closeFeedbackModal}
                style={modalStyles}
                contentLabel="Feedback Modal">
                <h4>Score Feedback</h4>
                <div style={{paddingBottom: '10px', fontWeight: 'bold'}}>
                    Your feedback will be used to help Bakround improve the accuracy of bScores.
                </div>
                <div>
                    Please let us know what score you think this candidate should have,
                    on a scale from 300 to 850:
                </div>
                <div style={{fontSize: '20px', fontWeight: 'bold'}}>
                    {this.state.sliderPosition}
                </div>
                <div style={{maxHeight: '100px'}}>
                    <InputSlider
                        className="slider slider-x"
                        axis="x"
                        xmin={300}
                        xmax={850}
                        x={parseInt(this.state.sliderPosition)}
                        onChange={this.changeSliderPosition} />
                     <table width="100%" style={{marginTop: '-15px'}}>
                        <tr>
                            <td style={{textAlign: 'left'}}>300</td>
                            <td style={{textAlign: 'right'}}>850</td>
                        </tr>
                     </table>
                </div>
                <form className="score_feedback_form">
                    <div>
                        Do you recommend interviewing this person for this job?
                        <input type="radio" name="should_interview" value="1" id="should_interview_yes" />
                        <label htmlFor="should_interview_yes" style={{marginLeft: '35px'}}>Yes</label>
                        <input type="radio" name="should_interview" value="" id="should_interview_no" />
                        <label htmlFor="should_interview_no" style={{marginLeft: '35px'}}>No</label>
                    </div>
	            
                    <div>
                        General comments (minimum 30 characters):<br/>
                        <textarea name="comment" rows="3" cols="50"></textarea>
                    </div>
	            
                    <div>
                        Please let us know which of these problems (if any) you have found with this candidate's profile:
                    </div>
	            
                    <div style={{textAlign: 'left', marginBottom: '30px'}}>
                        {[0, 1, 2, 3].map(i =>
                         <tr key={`bad_resume_option${i}`} className="input-field" style={{margin: '1px'}}>
                           <td style={{padding: '5px'}}>
                             <input type="checkbox" name={options[i].name} value="1"
                                 id={'checkbox_'+options[i].name}/>
                             <label htmlFor={'checkbox_'+options[i].name}
                                 style={{fontSize: '14px'}}>
                                 {options[i].text}
                             </label>
                           </td>
                           <td style={{minWidth: '20px', padding: '5px'}}></td>
                           <td style={{padding: '5px'}}>
                             <input type="checkbox" name={options[i+4].name} value="1"
                                 id={'checkbox_'+options[i+4].name}/>
                             <label htmlFor={'checkbox_'+options[i+4].name}
                                 style={{fontSize: '14px'}}>
                                 {options[i+4].text}
                             </label>
                           </td>
                         </tr>
                         )}
                    </div>
	            
                    <input type="button"
                           value="Submit"
                           onClick={this.submitFeedback}
                           style={{marginRight: '20px'}} />
	            
                    <input type="button"
                           value="Cancel"
                           onClick={this.closeFeedbackModal} />
                </form>
  	    </Modal>
        );
    }


    static make_status_modal() {
        /*
            call .bind(this) from Candidate before invoking
        */

  	const modalStyles = {
          content : {
            top        : '50%',
            left       : '50%',
            right      : 'auto',
            bottom     : 'auto',
            marginRight: '-50%',
            transform  : 'translate(-50%, -50%)',
            textAlign  : 'center'
          },
          overlay      : {zIndex: 1001}
        };

        let possible_statuses = this.state.possibleStatuses;
        let possible_reject_reasons = this.state.possibleRejectReasons;

        var status_select = null;
        if (possible_statuses && possible_reject_reasons) {
            let options = possible_statuses.map(record =>
                <option value={record.id}>{record.status}</option>);

            let default_option = <option value="">Select...</option>;
	    
            let reject_reason_options = possible_reject_reasons.map(record =>
                <option value={record.id}>{record.reason}</option>);
	    
            options = [default_option].concat(options);
            reject_reason_options = [default_option].concat(reject_reason_options);
	    
            status_select = (
                <form style={{margin: '30px'}}>
                    Change status:
                    <select name="new_status" className="new-status form-control"
                            onChange={(elt) => $(".reject-reason-div").css('display',
                                                    $(".new-status").val() == "3" ? 'block': 'none')}>
                        {options}
                    </select>
                    <br/>
                    <div className="reject-reason-div" style={{display: 'none'}}>
                        Reason for rejection:
                        <select name="reject_reason" className="form-control reject-reason">
                            {reject_reason_options}
                        </select>
                    </div>
                    <br/>
                    Notes (optional):
                    <br/>
                    <textarea id="new_status_notes" rows="5" cols="40"></textarea>
                    <br/>
                    <input type="button"
                           value="Change"
                           onClick={this.submitStatusForm}
                           />
                </form>
            );
        }

        return (
            <Modal
              isOpen={this.state.modalIsOpen}
              onAfterOpen={this.afterOpenModal}
              onRequestClose={this.closeModal}
              style={modalStyles}
              contentLabel="Candidate Status"
            >
              <div className='clearfix'>
                  <div className='pull-right'>
	              <span onClick={this.closeModal} className='fa fa-2x fa-window-close' style={{'color': '#57c1dc', 'cursor': 'pointer'}}>&nbsp;</span>
	    
                  </div>
              </div>
	    
              <h5>Edit Status</h5>
              <div style={{maxHeight: '200px', overflowY: 'scroll'}}>
                {(this.state.candidate_status || []).map(record =>
                    <div style={{marginTop: '15px', marginBottom: '15px'}}>
                        {record.status}
                        <br/>
                        <i>(set at {record.date} by {record.employer_user_name})</i>
                        {record.reject_reason && <span><br/><b>Reason:</b> {record.reject_reason}</span>}
                        {record.notes && <div style={{ maxWidth: '500px' }}><b>Notes: </b> {record.notes}</div>}
                    </div>
                )}
              </div>
	    
              {status_select}
            </Modal>
        );
    }
    
    static pushAdvancedSearchFilters(filters, params){
        let advancedSearchTypes = ["all", "any", "none"];
        let advancedSearchFilters = {
            all: {"key": "advanced_all"},
            any: {"key": "advanced_any"},
            none: {"key": "advanced_none"}
        };
        
        let _this = this;
    
        advancedSearchTypes.forEach(function (search_type){
            let filter = advancedSearchFilters[search_type];
            filter.value = params[search_type];
            filter.copy = _this.makeCopyForFilter(search_type, filter.value || "");
            if (params[search_type]) {
                filters.push(filter);
            }
        });
    }
    
    static makeCopyForFilter(search_type, filter_value){
        let capitalized_name = search_type.charAt(0).toUpperCase() + search_type.slice(1) + " of these words: ";
        if (filter_value.length > 30) {
            return capitalized_name + filter_value.substring(0, 50) + "...";
        } else {
            return capitalized_name + filter_value;
        }
    }
}
