import React from 'react';
import ReactDOM from 'react-dom';
import PubSub from 'pubsub-js';

import { runTour } from './tour';

import Networking from './networking';
import Pagination from './pagination';

import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import Snackbar from 'material-ui/Snackbar';
import Checkbox from 'material-ui/Checkbox';
import TextField from 'material-ui/TextField';

class ManualVerifier extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            page: 0,
            pageSize: 20,
            loading: false,
            requests: [],
            stats: [],
            total_requests: 0,
            filterBy: 'all'
        };

        this.pageClicked = this.pageClicked.bind(this);
        this.changeFilterBy = this.changeFilterBy.bind(this);

        this.getData = this.getData.bind(this);

        this.startTour = this.startTour.bind(this);
        this.tourCompleted = this.tourCompleted.bind(this);
        this.tourExited = this.tourExited.bind(this);

        this.verifyAllCheckedRequests = this.verifyAllCheckedRequests.bind(this);
        this.selectAllRequests = this.selectAllRequests.bind(this);
    }

    componentDidMount() {
        this.getData();
    }

    // UI Actions

    pageClicked(value) {
    	if (value === 'Next') {
            let _this = this;
            this.setState({page: this.state.page + 1}, () => _this.getData());
    	} else if (value === 'Previous') {
            let _this = this;
            this.setState({page: this.state.page - 1}, () => _this.getData());
    	}
    }

    changeFilterBy(e) {
        let _this = this;
        this.setState({ filterBy: e.target.value, page: 0 }, () => _this.getData());
    }

    // Networking

    getData() {
        this.setState({ loading: true });
        let _this = this;
        Networking.json("POST", "/manual_verifier/requests", {
            page: this.state.page,
            page_size: this.state.pageSize,
            filter: this.state.filterBy
        }).then(res => _this.setState({ requests: res.requests, stats: res.stats, total_requests: res.total_requests, loading: false }));
    }

    verifyAllCheckedRequests() {
        this.getSelectedRequestIds().forEach(i => {
            PubSub.publish('request_card.verify', { rid: i });
        });
        this.selectAllRequests(false);
    }

    selectAllRequests(goal) {
        $(".request-checkbox").find("input[type='checkbox']").each((i, elt) => {
            if ($(elt).is(":checked") !== goal) {
                $(elt).click();
            }
        });
    }

    getSelectedRequestIds() {
        var elements = $("div.request-checkbox input").get();
        return $.grep(elements, (elt, i) => $(elt).is(":checked"))
                .map((elt, i) => $(elt).data("rid"));
    }

    // Tour

    getTourSteps() {
        return [
            {
                intro: "Welcome to the manual verifier! We use it to complete incomplete profiles that our system can't.",
                position: "center"
            },
            {
                element: () => $('.bulk-controls')[0],
                intro: "Use these controls to perform bulk operations on the profiles below.",
                position: "bottom"
            },
            {
                element: () => $('.bulk-select')[0],
                intro: "These buttons will either select or deselect all profiles on the this page.",
                position: "bottom"
            },
            {
                element: () => $('.bulk-verify')[0],
                intro: "This button will verify all checked profiles immediately.",
                position: "bottom"
            },
            {
                element: () => $('.request-card')[0],
                intro: "Profiles show up in the manual verifier like this.",
                position: 'top'
            },
            {
                element: () => $('.request-verify')[0],
                intro: "Click this to verify a request. It will be removed from the verifier.",
                position: "top"
            },
            {
                element: () => $('.request-view-original')[0],
                intro: "View the original resume on Indeed (new tab). Copy any real name, emails, or phone numbers from the page into the corresponding profile. If you can't find anything, contact them using the form to the right of the resume body.",
                position: "top"
            },
            {
                element: () => $(".request-status-section")[0],
                intro: "These buttons/links control the status of the profile in the verifier. Clicking them toggles them. They will be blue if they are set, gray if they're unset.",
                position: "bottom"
            },
            {
                element: () => $('.request-contacted')[0],
                intro: "Click this if you contacted the profile using Indeed's contact form (right of resume body).",
                position: "bottom"
            },
            {
                element: () => $('.request-responded')[0],
                intro: "Click this if the profile responded to our inquiry on Indeed.",
                position: "bottom"
            },
            {
                element: () => $('.request-pending_action')[0],
                intro: "Click this if the profile needs manual intervention from a developer.",
                position: "bottom"
            },
            {
                element: () => $('.request-unreachable')[0],
                intro: "Click this if the profile cannot be reached through any means.",
                position: "bottom"
            },
            {
                element: () => $('.request-broken')[0],
                intro: "Click this if the profile is broken.",
                position: "bottom"
            },
            {
                element: () => $('.request-id-display')[0],
                intro: "This is the internal identifier of the profile in the manual verifier. Tell this number to developers to make them happy.",
                position: "right"
            },
            {
                element: () => $('.request-edit-name')[0],
                intro: "Click this to edit a profile's name.",
                position: "right"
            },
            {
                element: () => $('.request-job')[0],
                intro: "When contacting profiles externally (i.e. in Indeed), use this job name to pick a template.",
                position: "top"
            },
            {
                element: () => $('.request-address')[0],
                intro: "Street address of a profile. It's not essential information, but if it's there, add it.",
                position: "top"
            },
            {
                element: () => $('.request-phones')[0],
                intro: "Phone numbers at which to reach the profile. These are important, but not vital.",
                position: "top"
            },
            {
                element: () => $('.request-emails')[0],
                intro: "Email addresses at which to reach the profile. These are CRUCIAL!",
                position: "top"
            },
            {
                element: () => $('.save-button')[0],
                intro: "Click to immediately save the value of the input control next to it.",
                position: "right"
            },
            {
                element: () => $('.delete-button')[0],
                intro: "Click to immediately delete the value of the input control to the left of it.",
                position: "right"
            },
            {
                element: () => $('.add-button')[0],
                intro: "Click to add an element to a collection.",
                position: "right"
            },
            {
                element: () => $('#show_tour')[0],
                intro: "Click here to see this tour again.",
                position: "center"
            }
        ];
    }

    startTour() {
        runTour(this.getTourSteps());
    }

    render() {
        return (
            <MuiThemeProvider>
                <div>
                <h1 className="title-header" style={{fontSize: "36px", marginBottom: "5px"}}>
                    Manual Verifier
                    <sup>
                        <a style={{fontSize: "24px", padding: "5px"}}
                           className="fa fa-question-circle-o"
                           href="#!"
                           title="show tour"
                           onClick={this.startTour}
                           id="show_tour" />
                    </sup>
                </h1>
                <div className="manualVerifierStats">
                    <ul>
                        {this.state.stats.map((stat, i) => <li key={i}>{stat.name}: {stat.value}</li>)}
                    </ul>
                </div>
                <div className="manualVerifierBody">
                    {this.state.loading && <div style={{textAlign: "center"}}><i className="fa fa-2x fa-spinner fa-spin" /></div>}
                    {!this.state.loading &&
                     <div className="manualVerifierLoadedContent">
                         <span className='bulk-controls'>
                             <span className='bulk-select'>
                                 <a style={{margin: "10px 10px 10px 0px", cursor: 'pointer'}} onClick={() => this.selectAllRequests(true)}>Select All</a>
                                 <a style={{margin: "20px 20px 10px 10px", cursor: 'pointer'}} onClick={() => this.selectAllRequests(false)}>Deselect All</a>
                             </span>
                             |
                             <a className='bulk-verify' style={{margin: "10px 10px 20px 20px", cursor: 'pointer'}} onClick={this.verifyAllCheckedRequests}>Verify</a>
                         </span>
                         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                             <span>
        		         <span>Filter by: </span>
                    	         <select className='list-filter-dropdown' onChange={this.changeFilterBy} value={this.state.filterBy}>
                                     <option value="all">All</option>
                                     <option value='not_contacted'>Not Contacted</option>
                                     <option value='contacted'>Contacted</option>
                                     <option value='responded'>Responded</option>
                                     <option value='pending_action'>Pending Action</option>
                    	         </select>
                             </span>
                             <Pagination firstItem={(this.state.page * this.state.pageSize) + 1}
                                         lastItem={(this.state.page * this.state.pageSize) + this.state.requests.length}
                                         countItems={this.state.total_requests}
                                         pageClicked={this.pageClicked}
                                          />
                         </div>
                         {this.state.requests.map((r, i) => <RequestCard key={i} {...r} />)}
                         <Pagination firstItem={(this.state.page * this.state.pageSize) + 1}
                                     lastItem={(this.state.page * this.state.pageSize) + this.state.requests.length}
                                     countItems={this.state.total_requests}
                                     pageClicked={this.pageClicked}
                                     jumpToTop
                                      />
                     </div>}
                </div>
                </div>
            </MuiThemeProvider>
        );
    }
}

const styles = {
    card: {
        backgroundColor: "white",
        color: "grey",
        boxShadow: "0 0 0 1px rgba(0,0,0,.1), 0 2px 3px rgba(0,0,0,.2)",
        padding: "10px",
        margin: "10px 0px"
    },
    iconbutton: {
        margin: "5px",
        alignItems: "center",
        cursor: "pointer",
        fontSize: "20px"
    },
    iconbuttonContainer: {
        display: 'flex',
        alignItems: "center",
        zIndex: 20
    }
};

const EditButton = ({ onClick, className }) => <div className={className} style={styles.iconbuttonContainer}><i className="fa fa-pencil" aria-hidden="true" onClick={onClick} style={styles.iconbutton} /></div>;
const CancelButton = ({ onClick }) => <div style={styles.iconbuttonContainer}><i className="fa fa-times" aria-hidden="true" onClick={onClick} style={styles.iconbutton} /></div>;
const SaveButton = ({ onClick }) => <div className="save-button" style={styles.iconbuttonContainer}><i className="fa fa-save" aria-hidden="true" onClick={onClick} style={styles.iconbutton} /></div>;
const DeleteButton = ({ onClick }) => <div className="delete-button" style={styles.iconbuttonContainer}><i className="fa fa-trash" aria-hidden="true" onClick={onClick} style={styles.iconbutton} /></div>;
const AddButton = ({ onClick }) => <div className="add-button" style={styles.iconbuttonContainer}><i className="fa fa-plus" aria-hidden="true" onClick={onClick} style={styles.iconbutton} /></div>;
const LoadingIcon = ({ dimension }) => <div style={styles.iconbuttonContainer}><i className="fa fa-2x fa-spinner fa-spin" aria-hidden="true" style={Object.assign({}, styles.iconbutton, { fontSize: `${dimension}px` })} /></div>;

class TextValue extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            originalValue: this.props.value,
            currentValue: this.props.value,
            loading: false
        };

        this.markUpdated = this.markUpdated.bind(this);
        this.fireTimer = this.fireTimer.bind(this);
        this.onChange = this.onChange.bind(this);
        this.saveClicked = this.saveClicked.bind(this);
        this.deleteClicked = this.deleteClicked.bind(this);
    }

    markUpdated() {
        this.timeouts = [];
        this.setState({originalValue: this.state.currentValue, loading: false});
    }

    fireTimer() {
        let _this = this;
        _this.setState({loading: true});
    }

    onChange(e) {
        this.setState({ currentValue: e.target.value });
    }

    saveClicked(e) {
        if (this.props.save) {
            this.fireTimer();
            this.props.save(this.state.originalValue, this.state.currentValue, this.markUpdated);
        }
    }

    deleteClicked(e) {
        if (this.props.destroy) {
            this.fireTimer();
            this.props.destroy(this.state.originalValue, this.markUpdated);
        } else if (this.props.save) {
            this.fireTimer();
            this.props.save(this.state.originalValue, undefined, this.markUpdated);
        }
    }

    componentWillReceiveProps(nextProps) {
        this.setState({currentValue: nextProps.value});
    }

    render() {
        return (
            <div style={{ display: 'flex', alignItems: 'center' }}>
                {this.state.loading && <LoadingIcon dimension={20} />}
                {!this.state.loading && <div style={{ borderBottom: "1px solid transparent" }}><TextField inputStyle={this.props.label ? {} : {margin: 0}} style={{ margin: "0 5px" }} onChange={this.onChange} value={this.state.currentValue || ''} floatingLabelText={this.props.label}/></div>}
                {!this.state.loading && <SaveButton onClick={this.saveClicked} />}
                {!this.state.loading && this.props.showDelete && <DeleteButton onClick={this.deleteClicked} />}
            </div>
        );
    }
}

let statusDescs = [
    {display: "Contacted", name: "contacted" },
    {display: "Responded", name: "responded"},
    {display: "Pending Action", name: "pending_action"},
    {display: "Unreachable", name: "unreachable"},
    {display: "Broken", name: "broken"}
];

let cardstyles = {
    verify: {
        borderRadius: "22px",
        margin: "5px",
        height: "33px",
        width: "auto",
        padding: "0 15px",
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: "green",
        color: "white",
        fontWeight: "bold",
        cursor: "pointer",
        userSelect: 'none'
    },
    reallyVerify: {
        border: "2px green solid",
        borderRadius: "22px",
        margin: "5px",
        height: "33px",
        width: "auto",
        padding: "0 15px",
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: "white",
        color: "green",
        fontWeight: "bold",
        cursor: "pointer",
        userSelect: 'none'
    },
    fieldLabel: {
        width: "100px",
        display: 'flex',
        alignItems: 'center',
        height: "49px"
    }
};

class RequestCard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            // Data state
            status: this.props.status,
            job: this.props.job,
            profile: this.props.profile,
            resumeUrl: this.props.resume_url,
            id: this.props.id,

            // UI State
            checked: false,
            editingName: false,
            reallyVerify: false
        };

        this.verifyPS = this.verifyPS.bind(this);
        this.checkboxClicked = this.checkboxClicked.bind(this);
        this.editNameClicked = this.editNameClicked.bind(this);

        this.scalarUpdater = this.scalarUpdater.bind(this);
        this.vectorUpdater = this.vectorUpdater.bind(this);
        this.addVector = this.addVector.bind(this);
        this.toggleStatus = this.toggleStatus.bind(this);

        this.verify = this.verify.bind(this);
        this.notReallyVerify = this.notReallyVerify.bind(this);

        PubSub.subscribe("request_card.verify", this.verifyPS);
    }

    update(params, callback) {
        Networking.json("POST", "/manual_verifier/profiles/update", Object.assign({}, params, {profile_id: this.state.profile.id})).then(() => callback());
    }

    verifyPS(msg, { rid }) {
        if (rid === this.state.id) {
            this.setState({reallyVerify: true}, this.verify);
        }
    }

    checkboxClicked(e) {
        if (e) {
            e.stopPropagation();
        }

        if (this.props.setSelected) {
            this.props.setSelected(this.props.id, !this.state.checked);
        }
        this.setState({checked: !this.state.checked});
    }

    editNameClicked(e) {
        this.setState({ editingName: !this.state.editingName });
    }

    scalarUpdater(keyInProfile) {
        return ((_, newValue, markDone) => {
            let update = {};
            if (newValue && newValue.length > 0) {
                update[keyInProfile] = newValue;
            } else {
                update[keyInProfile] = null;
            }
            this.setState({ profile: Object.assign({}, this.state.profile, update)});
            this.update(update, markDone);
        }).bind(this);
    }

    vectorUpdater(keyInProfile) {
        return ((oldValue, newValue, markUpdated) => {
            let values = this.state.profile[keyInProfile];
            if (!values) values = [];
    
            let index = -1;
            index = values.indexOf(oldValue);
    
            if (newValue && newValue.length > 0) {
                if (index !== -1) {
                    values[index] = newValue;
                } else {
                    values.push(newValue);
                }
            } else {
                if (index !== -1) {
                    values.splice(index, 1);
                }
            }
    
            let stateUpdate = {};
            stateUpdate[keyInProfile] = values;

            this.setState({ profile: Object.assign({}, this.state.profile, stateUpdate)});
    
            let entry = {};
            if (oldValue && oldValue.length > 0) entry.old_value = oldValue;
            if (newValue && newValue.length > 0) entry.new_value = newValue;
            
            let backendUpdate = {};
            backendUpdate[keyInProfile] = [entry];

            this.update(backendUpdate, markUpdated);
        }).bind(this);
    }

    addVector(name) {
        return (() => {
            let d = {};
            d[name] = (this.state.profile[name] || []).concat([null]);
            this.setState({ profile: Object.assign({}, this.state.profile, d)});
        }).bind(this);
    }

    toggleStatus(field) {
        return (() => {
            let d = {};
            d[field] = !this.state.status[field];
            Networking.json("POST", "/manual_verifier/requests/update_status", Object.assign({}, d, { request_id: this.state.id  }));
            this.setState({ status: Object.assign({}, this.state.status, d) });
        }).bind(this);
    }

    verify() {
        if (!this.state.reallyVerify) {
            this.setState({ reallyVerify: true });
        } else {
            Networking.json("POST", "/manual_verifier/requests/verify", { request_id: this.state.id });
            this.setState({ status: Object.assign({}, this.state.status, { verified: true }), reallyVerify: false });
        }
    }

    isVerified() {
        return this.state.status.verified;
    }

    notReallyVerify() {
        this.setState({reallyVerify: false});
    }

    render() {
        let _this = this;
        return (
            <div className="request-card" style={Object.assign({}, styles.card, this.isVerified() ? { pointerEvents: 'none', userSelect: 'none', opacity: '0.5', backgroundColor: '#EFFFEF' } : {})}>
                <div className="action-top-bar" style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', flexWrap: "wrap" }}>
                    <Checkbox
                        key={this.state.id}
                        data-rid={this.state.id}
                        className="request-checkbox"
                        style={{width: 'inherit', height: 'inherit', marginRight: "-11.5px"}}
                        inputStyle={{pointerEvents: this.isVerified() ? "none" : "all"}}
                        onClick={this.checkboxClicked} />
                    <a className="request-verify" style={this.state.reallyVerify ? cardstyles.reallyVerify : cardstyles.verify} onClick={this.verify}>
                        {this.isVerified() ? "Verified" : (this.state.reallyVerify ? "Really Verify?" : "Verify")}
                    </a>
                    {this.state.resumeUrl && <a style={{borderRadius: "22px", margin: "5px", height: "33px", width: "auto", padding: "0 15px", display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: "#00548b", color: "white", fontWeight: "bold", cursor: "pointer", userSelect: 'none' }} href={this.state.resumeUrl} target="_blank" className="request-view-original">
                        View Original
                    </a>}
                    <div style={{ marginLeft: "auto"}} />
                    <div className="request-status-section" style={{display: 'flex'}}>
                        {statusDescs.map((d, i) =>
                        <a key={i} onClick={this.toggleStatus(d.name)} style={{ margin: "10px", color: (this.state.status[d.name] ? "#039be5" : "gray"), cursor: "pointer" }} className={`request-${d.name}`}>
                            {d.display}
                        </a>)}
                    </div>
                </div>
                <div className='requestInfoContainer'>
                    <div className='requestProfile' style={{ display: 'flex', flexDirection: 'column' }}>
                        {!this.state.editingName &&
                         <div style={{display: 'flex', alignItems: 'center' }}>
                             <span style={{ fontSize: "24px", margin: "10px 0" }}>
                                 <span style={{ marginRight: "10px" }} className="request-id-display"><b>#{this.state.id}</b></span>{this.state.profile.first_name} {this.state.profile.middle_name} {this.state.profile.last_name}
                             </span>
                             <div style={{margin: "10px"}}>
                                 <EditButton onClick={this.editNameClicked} className="request-edit-name" />
                             </div>
                         </div>}
                         {this.state.editingName &&
                          <div style={{ display: 'flex', flexDirection: "row", alignItems: "flex-start" }} >
                              <div style={{ display: 'flex', flexDirection: "column" }}>
                                  {[{display: "FIRST", name: "first_name" },{display: "MIDDLE", name: "middle_name"}, {display: "LAST", name: "last_name"}].map((d, i) =>
                                   <div key={i} className="request-first-name" style={{ display: 'flex', alignItems: "flex-start", margin: '10px 0' }}>
                                       <span style={cardstyles.fieldLabel}>{d.display}</span>
                                       <TextValue
                                           value={this.state.profile[d.name] || undefined}
                                           save={this.scalarUpdater(d.name)} />
                                   </div>)}
                              </div>
                              <CancelButton onClick={this.editNameClicked} className="request-cancel-button" />
                          </div>
                          }
                          <div className="request-profile-info">
                              {this.state.job && <div className="request-job" style={{ display: 'flex', alignItems: "flex-start", margin: '10px 0' }}>
                                  <span style={cardstyles.fieldLabel}>JOB</span>
                                  <span>
                                      {this.state.job.title === this.state.job.generic_title ? this.state.job.title : `${this.state.job.title} (${this.state.job.generic_title})`} @ {this.state.job.company_name}
                                  </span>
                              </div>}
                              <div className="request-address" style={{ display: 'flex', alignItems: "flex-start", margin: '10px 0' }}>
                                  <span style={cardstyles.fieldLabel}>ADDRESS</span>
                                  <TextValue
                                      value={this.state.profile.street_address || undefined}
                                      save={this.scalarUpdater("street_address")} />
                              </div>
                              <div className="request-phones" style={{display: 'flex', alignItems: "flex-start", margin: '10px 0' }}>
                                  <span style={cardstyles.fieldLabel}>PHONE</span>
                                  <div>
                                      {this.state.profile.phones.map((p, i) => 
                                       <TextValue
                                           value={p}
                                           key={i}
                                           save={this.vectorUpdater("phones")} showDelete />)}
                                       <AddButton onClick={this.addVector("phones")}/>
                                  </div>
                              </div>
                              <div className="request-emails" style={{display: 'flex', alignItems: "flex-start", margin: '10px 0' }}>
                                  <span style={cardstyles.fieldLabel}>EMAIL</span>
                                  <div>
                                      {this.state.profile.emails.map((e, i) => 
                                       <TextValue
                                           value={e}
                                           key={i}
                                           save={this.vectorUpdater("emails")} showDelete />)}
                                      <AddButton onClick={this.addVector("emails")} />
                                  </div>
                              </div>
                          </div>
                    </div>
                </div>
            </div>
        );
    }
}

ReactDOM.render(
    <ManualVerifier {...JSON.parse(window.props)} />,
    window.react_mount
);
