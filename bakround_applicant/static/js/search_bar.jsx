import React from 'react';
import ReactDOM from 'react-dom';

import Dialog from 'material-ui/Dialog';
import FlatButton from 'material-ui/FlatButton';
import { RadioButton, RadioButtonGroup } from 'material-ui/RadioButton';

import indexOf from 'lodash/indexOf';
import find from 'lodash/find';
import includes from 'lodash/includes';
import filter from 'lodash/filter';
import uniqWith from 'lodash/uniqWith';
import isEqual from 'lodash/isEqual';

import Modal from 'react-modal';
import CandidateUtil from './candidate_util';

const DISTANCE_LIST = [
    {value: 200, copy: 'less than 200 miles'},
    {value: 100, copy: 'less than 100 miles'},
    {value: 50, copy: 'less than 50 miles'},
    {value: 20, copy: 'less than 20 miles'},
    {value: 10, copy: 'less than 10 miles'},
    {value: -10, copy: 'greater than 10 miles'},
    {value: -20, copy: 'greater than 20 miles'},
    {value: -50, copy: 'greater than 50 miles'},
    {value: -100, copy: 'greater than 100 miles'},
    {value: -200, copy: 'greater than 200 miles'},
];

const score_list = [
    {label: 'Minimal Fit or better', min: 300, max: 409},
    {label: 'Some Fit or better', min: 410, max: 519},
    {label: 'Good Fit or better', min: 520, max: 629},
    {label: 'Great Fit or better', min: 630, max: 739},
    {label: 'Best Fit', min: 740, max: 850}
];

const experience_list = [
    {'years': 1, 'months':12},
    {'years': 3, 'months':36},
    {'years':5, 'months': 60},
    {'years':7, 'months': 84},
    {'years':9, 'months': 108}
];

const education_list = ['Highschool', 'Associates', 'Bachelors', 'Masters', 'Doctorate'];

export default class SearchBar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {filters: props.filters,
        	ordering: props.ordering,
        	page_size: props.page_size,
        	state_list: this.props.state_list,
        	advancedSearchModalIsOpen: false,
        	advanced: this.props.advanced};

     	this.filterClicked = this.filterClicked.bind(this);

        this.openAdvancedSearchModal = this.openAdvancedSearchModal.bind(this);
        this.afterOpenAdvancedSearchModal = this.afterOpenAdvancedSearchModal.bind(this);
        this.closeAdvancedSearchModal = this.closeAdvancedSearchModal.bind(this);
    }

    setOrdering() {
    	let value = ReactDOM.findDOMNode(this.refs.sortBySelect).value;
        let _this = this;
    	this.setState({ordering: value}, () => {
            if (_this.props.orderingChanged) {
                _this.props.orderingChanged(_this.state.ordering);
            }
        });
    }

    setPageSize() {
    	let value = ReactDOM.findDOMNode(this.refs.setPageSize).value;
        let _this = this;
    	this.setState({page_size: value}, () => {
            if (_this.props.pageSizeChanged) {
                _this.props.pageSizeChanged(_this.state.page_size);
            }
        });
    }

    filterClicked(id, key, value, copy=false) {
    	let newFilter = {};
    	newFilter.key = key;
    	newFilter.value = value;
    	newFilter.copy = copy || value;
    	newFilter.id = id;
    	let filterState = this.state.filters;
    	let index = indexOf(filterState, find(filterState, {key: key}));
    	let singleFilter = ['location', 'job_id', 'distance', 'score', 'experience', 'min_education', 'state_filter'];
    	if (singleFilter.includes(newFilter.key) && index > -1) {
            filterState.splice(index, 1, newFilter);
    	} else {
            filterState = uniqWith(this.state.filters.concat(newFilter), isEqual);
      	}
        let _this = this;
        this.setState({filters: filterState}, () => {
            if (_this.props.filtersChanged) {
                _this.props.filtersChanged(_this.state.filters);
            }
        });
    }

    removeFilter(filterIndex) {
    	this.state.filters.splice(filterIndex, 1);
        let _this = this;
        this.setState({filters: this.state.filters}, () => {
            if (_this.props.filtersChanged) {
                _this.props.filtersChanged(_this.state.filters);
            }
        });
    }

    clearDropdown(ref_dom_input, all_options, state_field) {
    	ReactDOM.findDOMNode(this.refs[ref_dom_input]).value = '';
    	this.setState({[state_field]: all_options});
    }

    filterDropdown(ref_dom_input, all_options, field, state_field) {
    	let value = ReactDOM.findDOMNode(this.refs[ref_dom_input]).value;
    	let filtered_opts = all_options.filter((opt, index) => {
    	    let v = field ? opt[field] : opt;
    	    return includes(v.toLowerCase(), value.toLowerCase());
    	});
    	this.setState({[state_field]: filtered_opts});
    }

    render() {
    	let _this = this;
    	let search_bar_content = null;
    	if (this.state.filters.length > 0) {
    		search_bar_content = this.state.filters.map((filter, index) =>
    		    <FilterChip key={index} filter_key={filter.key} value={filter.copy || filter.value} onClick={(i) => _this.removeFilter(index)} />);
    	} else {
    		search_bar_content = <div className='search-placeholder-text'>Select filters to get searching</div>;
    	}

    	let searchBy = <span>
            	<span style={{fontWeight: 'bold', marginLeft: '30px'}}>Sort by: </span>
            	<select className='list-filter-dropdown' ref="sortBySelect" onChange={(i) => this.setOrdering()}
            	value={this.state.ordering}>
            		<option value='score'>bScore</option>
            		<option value='distance'>distance</option>
            		<option value='experience'>experience</option>
            		<option value='last_updated_date'>last updated date</option>
            	</select>
    	    </span>;

        return (
            <div>
        	<div className='search-filter-container'>
        		<div id='search-bar' className='search-bar display-flex align-items-center'>
        			<i className='fa fa-2x fa-search' style={{color: 'grey', margin: '0px 10px'}}></i>
        				{search_bar_content}
        		</div>
        		<div className='filter-bar display-flex'>
        			<div className="dropdown filter-mobile-hide">
        			  	<button className="btn-default dropdown-toggle" type="button" id="scoreDropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true"> Score&nbsp;
        			    	<span className="caret"></span>
        			  	</button>
        			  	<ul className="dropdown-menu" aria-labelledby="scoreDropdown">
        			  		{score_list.map((score, index) =>
    	                                        	<li key={index}>
    	                                        		<a onClick={() => _this.filterClicked(index, 'score', score.min, 'bScore: ' + score.label + ' (' +score.min + ')')} className="dropdown-item" href="#!"> {score.label} ({score.min} min)</a>
    	                                        	</li>
    	                                        )}
        			  	</ul>
        			</div>
        			<div className="dropdown filter-mobile-hide">
        			  	<button className="btn-default dropdown-toggle" type="button" id="distanceDropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true"> Distance&nbsp;
        			    	<span className="caret"></span>
        			  	</button>
        			  	<ul className="dropdown-menu" aria-labelledby="distanceDropdown">
        			  		{DISTANCE_LIST.map((distance, index) =>
                                                    <li key={index}>
                                                        <a onClick={() => _this.filterClicked(index, 'distance', distance.value, distance.copy)} className="dropdown-item" href="#!">{distance.copy}</a>
                                                    </li>
                                                )}
        			  	</ul>
        			</div>
        			<div className="dropdown filter-mobile-hide">
        			  	<button className="btn-default dropdown-toggle" type="button" id="experienceDropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">Education&nbsp;
        			    	<span className="caret"></span>
        			  	</button>
        			  	<ul className="dropdown-menu" aria-labelledby="experienceDropdown">
        			  		{education_list.map((edu, index) =>
    	                                        	<li key={index}>
    	                                        		<a onClick={() => _this.filterClicked(index, 'min_education', edu.toLowerCase(), 'Min Education: ' + edu)} className="dropdown-item" href="#!" key={index}>{edu} </a>
    	                                        	</li>
    	                                        )}
        			  	</ul>
        			</div>
        			<div className="dropdown filter-mobile-hide">
        			  	<button className="btn-default dropdown-toggle" type="button" id="experienceDropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">Experience&nbsp;
        			    	<span className="caret"></span>
        			  	</button>
        			  	<ul className="dropdown-menu dropdown-menu-right" aria-labelledby="experienceDropdown">
        			  		{experience_list.map((experience, index) =>
    	                                        	<li key={index}>
    	                                        		<a onClick={() => _this.filterClicked(index, 'experience', experience.months, experience.years.toString().concat('+ years of experience'))} className="dropdown-item" href="#!">{experience.years}+ years</a>
    	                                        	</li>
    	                                        )}
        			  	</ul>
        			</div>
        			<div className="dropdown">
        			  	<button className="btn-default dropdown-toggle" type="button" id="stateDropdown" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true"> State&nbsp;
        			    	<span className="caret"></span>
        			  	</button>
        			  	<ul className="dropdown-menu scrollable-menu" aria-labelledby="stateDropdown">
        			  		{this.state.state_list.map((state, index) =>
                                                	<li key={index}>
                                                		<a onClick={() => _this.filterClicked(state.id, 'state_filter', state.id, 'State: ' + state.state_code)} className="dropdown-item" href="#!">{state.state_code}</a>
                                                	</li>
                                                )}
        			  	</ul>
        			</div>
        			<div className='mobile-filters'>
        				<MobileFilterDialog filterClicked={this.filterClicked} score_list={score_list} distance_list={DISTANCE_LIST} experience_list={experience_list} education_list={education_list}/>
        			</div>
        		</div>
        		{this.props.showAdvancedSearch && <a href="#!" onClick={this.openAdvancedSearchModal}
        		   id="advanced_search_link"
        		   style={{paddingLeft: '5px', paddingTop: '5px', fontWeight: 'bold', 'float': 'left'}}
        		   >Advanced Search...</a>}
        	</div>
        	{this.props.includeSortBy &&
        	<div className='text-right'>
                        {searchBy}
                        {<span>
                            <span style={{fontWeight: 'bold', marginLeft: '20px'}}> # of candidates per page:</span>
                            <select className='list-filter-dropdown' ref="setPageSize" onChange={(i) => this.setPageSize()}
                            value={this.state.page_size || 20}>
                                <option value="20">20</option>
                                <option value="50">50</option>
                            </select>
                        </span>}
        	</div>
        	}
        	{this.makeAdvancedSearchModal()}
            </div>
        );
    }

    makeAdvancedSearchModal(){
        const modalStyles = {
          content : {
            top                   : '50%',
            left                  : '50%',
            right                 : 'auto',
            bottom                : 'auto',
            marginRight           : '-50%',
            transform             : 'translate(-50%, -50%)',
            textAlign             : 'center',
            minWidth              : '500px'
          },
          overlay                 : {zIndex: 1001}
        };

        return <Modal
                   isOpen={this.state.advancedSearchModalIsOpen}
                   onAfterOpen={this.afterOpenAdvancedSearchModal}
                   onRequestClose={this.closeAdvancedSearchModal}
                   style={modalStyles}
                   contentLabel="Example Modal">
            <div>
                All of these words: &nbsp;
                <input id="advanced_all" type="text"
                       style={{display: 'inline-block', width: '250px'}}
                       />
            </div>
            <div>
                Any of these words: &nbsp;
                <input id="advanced_any" type="text"
                       style={{display: 'inline-block', width: '250px'}}
                       />
            </div>
            <div>
                None of these words: &nbsp;
                <input id="advanced_none" type="text"
                       style={{display: 'inline-block', width: '250px'}}
                       />
            </div>
            <div>
                <input type="button" onClick={this.closeAdvancedSearchModal} value="OK"/>
            </div>
        </Modal>;
    }

    openAdvancedSearchModal(){
        this.setState({advancedSearchModalIsOpen: true}, () =>
            this.fillInAdvancedSearchModalBoxes());
    }

    closeAdvancedSearchModal(){
        this.setState({advancedSearchModalIsOpen: false});
        this.setAdvancedSearchParameters();
    }

    afterOpenAdvancedSearchModal(){
    }

    setAdvancedSearchParameters(){
        let params = {
            "all": $("#advanced_all").val().trim(),
            "any": $("#advanced_any").val().trim(),
            "none": $("#advanced_none").val().trim()
        };

        if (params.all || params.any || params.none){
            this.setState({advanced: params});
        } else {
            this.setState({advanced: null});
        }

        this.showAdvancedSearchPills(params);
    }

    fillInAdvancedSearchModalBoxes(){
        let params = this.state.advanced || {};
        $("#advanced_all").val(params.all || "");
        $("#advanced_any").val(params.any || "");
        $("#advanced_none").val(params.none || "");
    }

    showAdvancedSearchPills(params){
        let filters = filter(this.state.filters, filter => filter.key.indexOf("advanced") != 0);

        CandidateUtil.pushAdvancedSearchFilters(filters, params);

        let _this = this;
        this.setState({filters: filters}, () => {
            if (_this.props.filtersChanged) {
                _this.props.filtersChanged(_this.state.filters);
            }
        });
    }
}

class FilterChip extends React.Component {
    render() {
        var chip = <span>{this.props.value}</span>;
	let remove_chip = null;
	if (this.props.filter_key !== 'job_id' && this.props.filter_key !== 'location' && this.props.filter_key !== 'distance' && this.props.filter_key.indexOf('advanced') != 0) {
	    remove_chip = <span className='remove-filter-pill' onClick={this.props.onClick}> X </span>;
	}

        if (this.props.filter_key.indexOf('advanced') === 0) {
	    return <div style={{width: '100%'}}><span className='filter-pill'> {chip} {remove_chip}</span></div>;
	} else {
	    return <span className='filter-pill'> {chip} {remove_chip}</span>;
	}
    }
}

class MobileFilterDialog extends React.Component {
  	constructor() {
	    super();
	    this.state = {
                open: false,
                score: '',
                distance: 50,
	    	min_education: '',
                experience: ''
            };
	    this.handleOpen = this.handleOpen.bind(this);
	    this.handleClose = this.handleClose.bind(this);
	    this.filterChange = this.filterChange.bind(this);
	}

  	handleOpen() {
	    this.setState({open: true});
  	}

  	handleClose() {
	    this.setState({open: false});
  	}

  	filterChange(event, value) {
            let copy = event.target.getAttribute('data-filter-copy');
            let key = event.target.getAttribute('data-key');
            value = key == 'min_education' ? value.toLowerCase() : value;
            this.props.filterClicked('index', key, value, copy);
            var newState = {};
            newState[key] = value;
            this.setState(newState);
	}

  	render() {
  		const RadioOptionLabelStyle = {
  			'fontWeight': 300,
  			'fontSize': '1rem'
  		};

  		const RadioContainerLabelStyle = {
  			'fontWeight': 500,
  			'padding': '10px 0px 0px'
  		};
	    const actions = [
	      <FlatButton
	        label="Close"
	        primary={true}
	        onClick={this.handleClose}
	      />
	    ];

	    const education_radios = [];
	    this.props.education_list.map((edu,i) => {
	      education_radios.push(
	        <RadioButton
	          key={i}
	          labelStyle={RadioOptionLabelStyle}
	          value={edu.toLowerCase()}
	          label={edu}
	          data-key='min_education'
	          data-filter-copy={`Min Education: ${edu}`}
	        />
	      );
	    });

  	  const distance_radios = [];
	    this.props.distance_list.map((distance,i) => {
	      distance_radios.push(
	        <RadioButton
	          key={i}
	          labelStyle={RadioOptionLabelStyle}
	          value={distance.value}
	          label={`${distance.value} miles`}
	          data-key='distance'
	          data-filter-copy={`${distance.value} miles`}
	        />
	      );
	    });

	    const experience_radios = [];
	    this.props.experience_list.map((experience,i) => {
	    	experience_radios.push(
	        <RadioButton
	          key={i}
	          labelStyle={RadioOptionLabelStyle}
	          style={RadioOptionLabelStyle}
	          value={experience.months}
	          label={`${experience.years}+ years of experience`}
	          data-key='experience'
	          data-filter-copy={`${experience.years}+ years of experience`}
	        />
	      );
	    });

	    const score_radios = [];
	    this.props.score_list.map((score,i) => {
	      score_radios.push(
	        <RadioButton
        	  labelStyle={RadioOptionLabelStyle}
	          key={i}
	          value={score.min}
	          data-key='score'
	          data-filter-copy={`bScore: ${score.label} (${score.min})`}
	          label={`${score.label} (min ${score.min})`}
	        />
	      );
	    });

	    return (
	      <div>
	      	<div onClick={this.handleOpen}><i className='fa fa-sliders'></i></div>
	        <Dialog
	          title="Filters"
	          actions={actions}
	          modal={true}
	          open={this.state.open}
	          onRequestClose={this.handleClose}
	          autoScrollBodyContent={true}
	        >
          		<p style={RadioContainerLabelStyle}> Min Score </p>
  	         	<RadioButtonGroup name="score" defaultSelected={this.state.score} onChange={this.filterChange}>
	            	{score_radios}
	          	</RadioButtonGroup>
	        	<p style={RadioContainerLabelStyle}> Max Distance </p>
          		<RadioButtonGroup name="distance" defaultSelected={this.state.distance} onChange={this.filterChange}>
	            	{distance_radios}
          		</RadioButtonGroup>
          		<p style={RadioContainerLabelStyle}> Min Education </p>
  	         	<RadioButtonGroup name="education" defaultSelected={this.state.min_education} onChange={this.filterChange}>
	            	{education_radios}
	          	</RadioButtonGroup>
        		<p style={RadioContainerLabelStyle}> Min Years of Experience </p>
  	         	<RadioButtonGroup name="experience" defaultSelected={this.state.experience} onChange={this.filterChange}>
	            	{experience_radios}
	          	</RadioButtonGroup>
	        </Dialog>
	      </div>
	    );
  	}
}
