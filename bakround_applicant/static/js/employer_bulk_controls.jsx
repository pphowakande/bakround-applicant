import React from 'react';
import PubSub from 'pubsub-js';
import Candidate from './candidate';

class EmployerBulkControls extends React.Component {
    constructor(props) {
        super(props);
        this.state = { selectedCount: 0 };
        this.handlePubSubEvent = this.handlePubSubEvent.bind(this);
        PubSub.subscribe('bulk_controls.increment', this.handlePubSubEvent);
        PubSub.subscribe('bulk_controls.decrement', this.handlePubSubEvent);
    }

    handlePubSubEvent(msg, data) {
        if (msg === 'bulk_controls.increment') {
            this.setState(st => ({selectedCount: st.selectedCount + 1}));
        } else if (msg === 'bulk_controls.decrement') {
            this.setState(st => ({selectedCount: st.selectedCount - 1}));
        }
    }

    render() {
        return (
           <div className="bulk-controls">
               <a href="#!" onClick={i => Candidate.setAllChecked(true)}
                  className="candidate-select-action"
                  >Select All</a>&nbsp;
               <a href="#!" onClick={i => Candidate.setAllChecked(false)}
                  className="candidate-select-action"
                  >Deselect All</a>&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
               <a href="#!" onClick={i => Candidate.contactChecked()}
                  className={`candidate-select-action contact_selected_candidates_link ${this.state.selectedCount > 0 ? '' : 'grayed-out-link'}`}
                  >Send Intro</a>
           </div>
        );
    }
}

export default EmployerBulkControls;
