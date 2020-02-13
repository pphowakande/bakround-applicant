import sys
from .sanitation import SanitationRanking
import json
import requests
import time
import datetime
from bakround_applicant.scraping.indeed_html_parser.parser import parse_results
from bakround_applicant.scraping.indeed_html_parser.sanitation import Sanitation
from bakround_applicant.all_models.db import ProfileResume


def get_people_data(url):
    applicant_workflow_endpoint = url

    # create sanitation object
    sanitation_obj = SanitationRanking()
    sanitation_obj1 = Sanitation()

    # generate request headers
    headers = sanitation_obj.generate_request_headers()

    payload1 = ""
    response1 = requests.request("GET", applicant_workflow_endpoint,data=payload1, headers=headers)
    if response1.status_code == 200:
        # got people ids related to applicant workflows
        response1 = response1.json()

        associatedprofile = response1["associatedprofile"]["profile"]
        associatedprofile_id =  response1["associatedprofile"]["id"]
        associatedprofile_name = response1["associatedprofile"]["value"]

        # save data in database and then seach for each profile details
        job_baseprofile = response1["baseprofile"]["profile"]
        job_title = response1["baseprofile"]["value"]
        print("job_title : ", job_title)

        # save job title and link in database
        sanitation_obj.save_icims_job(job_baseprofile,job_title)

        # get applicant_workflow_id using applicant_workflow_endpoint
        applicant_workflow_id = applicant_workflow_endpoint.split("applicantworkflows/")[1]

        # product_name,workflow_id,workflow_url,person_id,person_name,person_url,job_url
        sanitation_obj.save_applicant_workflow(applicant_workflow_id,applicant_workflow_endpoint,associatedprofile_id,associatedprofile_name,associatedprofile,job_baseprofile)

        results = {}

        # save icims job data
        baseprofile_value = response1["baseprofile"]["value"]
        baseprofile_id = response1["baseprofile"]["id"]

        results["icims_job"] = []
        icims_job = {}
        icims_job["value"] = baseprofile_value
        icims_job["id"] = baseprofile_id
        icims_job["job"] = job_baseprofile
        results["icims_job"].append(icims_job)

        # get people data
        querystring = {"fields":"workexperience,skillset,licensecertification,education,firstname,lastname,middlename,addresses,phones,email,gender"}
        payload = ""
        people_response = requests.request("GET", associatedprofile, data=payload, headers=headers, params=querystring)
        people_response = people_response.json()

        # save gender, email and phones data

        if 'email' in people_response:
            results['email'] = people_response["email"]
        else:
            results['email'] = ""

        if 'gender' in people_response:
            results['gender'] = people_response["gender"]
        else:
            results['gender'] = ""

        results['phones'] = []
        if 'phones' in people_response:
            if len(people_response["phones"]) > 0:
                for each_phone in people_response["phones"]:
                    phone_dict = {}
                    if 'phonetype' in each_phone:
                        if 'value' in each_phone['phonetype']:
                            phone_dict["phone_type"] = each_phone["phonetype"]["value"]
                        elif 'formattedvalue' in each_phone['phonetype']:
                            phone_dict["phone_type"] = each_phone["phonetype"]["formattedvalue"]
                    else:
                        phone_dict["phone_type"] = ""
                    if 'phonenumber' in each_phone:
                        phone_dict["phone"] = each_phone["phonenumber"]
                    else:
                        phone_dict["phone"] = ""
                    results["phones"].append(phone_dict)

        results['street_address'] = ""

        # get location
        if 'addresses' in people_response:
            addresses = people_response["addresses"]
            if len(addresses) > 0:
                if 'addresscity' in addresses[0]:
                    results['city'] = addresses[0]["addresscity"]
                else:
                    results['city'] = ""
                if 'addressstate' in addresses[0]:
                    if 'abbrev' in addresses[0]["addressstate"]:
                        state = sanitation_obj.extract_state(addresses[0]["addressstate"]["abbrev"])
                    elif 'value' in addresses[0]["addressstate"]:
                        state = sanitation_obj.extract_state(addresses[0]["addressstate"]["value"])
                    else:
                        state = ""
                else:
                    state = ""

                if 'addressstreet1' in addresses[0]:
                    street_address = addresses[0]["addressstreet1"]
                    results['street_address'] = street_address
                else:
                    results['street_address'] = ""
                results['state_code'] = state.state_code if state else None
            else:
                results['city'] = ""
                results['state_code'] = ""
                results['street_address']
        else:
            results['city'] = ""
            results['state_code'] = ""
            results['street_address']

        # get basic Information
        if 'firstname' in people_response:
            results['first_name'] = people_response["firstname"]
        else:
            results['first_name'] = ""
        if 'middlename' in people_response:
            results['middle_name'] = people_response["middlename"]
        else:
            results['middle_name'] = ""
        if 'lastname' in people_response:
            results['last_name'] = people_response["lastname"]
        else:
            results['last_name'] = ""

        # get additional_information
        results['additional_information'] = ""
        # get summary
        results["summary"] = ""
        # get groups
        results["groups"] = []
        # get awards
        results["awards"] = []

        # get education
        results['education'] = []
        if 'education' in people_response:
            educations = people_response["education"]
            if len(educations) > 0:
                for education in educations:
                    temp = {}
                    if 'degree' in education:
                        if 'formattedvalue' in education["degree"]:
                            degree = education["degree"]["formattedvalue"]
                            temp['degree_name'] = degree
                            temp['degree_type'] = sanitation_obj1.guess_degree_type(degree)
                            temp['degree_major'] = degree
                        elif 'value' in education:
                            degree = education["degree"]["value"]
                            temp['degree_type'] = sanitation_obj1.guess_degree_type(degree)
                            temp['degree_major'] = degree
                        else:
                            temp['degree_name'] = ""
                            temp['degree_type'] = ""
                            temp['degree_major'] = ""
                    else:
                        temp['degree_name'] = ""
                        temp['degree_type'] = ""
                        temp['degree_major'] = ""

                    if 'major' in education:
                        if 'formattedvalue' in education["major"]:
                            temp['degree_major'] = education["major"]["formattedvalue"]
                        elif 'value' in education["major"]:
                            temp['degree_major'] = education["major"]["value"]
                        else:
                            temp["degree_major"] = ""
                    else:
                        temp["degree_major"] = ""

                    if 'school' in education:
                        if 'formattedvalue' in education["school"]:
                            temp['school_name'] = education["school"]["formattedvalue"]
                        elif 'value' in education["school"]:
                            temp['school_name'] = education["school"]["value"]
                        else:
                            temp["school_name"] = ""
                    else:
                        temp["school_name"] = ""

                    if 'graduationdate' in education:
                        temp['degree_date'] = education['graduationdate']
                        temp['end_date'] = education['graduationdate']
                    else:
                        temp['degree_date'] = ""
                        temp['end_date'] = ""

                    if 'educationstartdate' in education:
                        temp['start_date'] = education['educationstartdate']
                    else:
                        temp['start_date'] = ""

                    if 'educationcity' in education:
                        temp["city_name"] = education["educationcity"]
                    else:
                        temp["city_name"] = ""

                    if 'educationstate' in education:
                        if 'abbrev' in education["educationstate"]:
                            state = sanitation_obj.extract_state(education["educationstate"]["abbrev"])
                        elif 'value' in education["educationstate"]:
                            state = sanitation_obj.extract_state(education["educationstate"]["value"])
                        else:
                            state = ""
                        temp['state_code'] = state.state_code if state else None
                    else:
                        temp["state_code"] = ""

                    results['education'].append(temp)

        # get experience
        results['experience'] = []
        if 'workexperience' in people_response:
            experiences = people_response["workexperience"]
            if len(experiences) > 0:
                counter = 0
                for experience in experiences:
                    temp = {}
                    if 'worktitle' in experience:
                        temp["job_title"] = experience["worktitle"]
                    else:
                        temp["job_title"] = ""
                    if 'workemployer' in experience:
                        temp["company_name"] = experience["workemployer"]
                    else:
                        temp["company_name"] = ""
                    if 'workcity' in experience:
                        temp["city_name"] = experience["workcity"]
                    else:
                        temp["city_name"] = ""
                    if 'workstate' in experience:
                        if 'abbrev' in experience["workstate"]:
                            state = sanitation_obj.extract_state(experience["workstate"]["abbrev"])
                        elif 'value' in experience["workstate"]:
                            state = sanitation_obj.extract_state(experience["workstate"]["value"])
                        else:
                            state = ""
                        temp['state_code'] = state.state_code if state else None
                    else:
                        temp['state_code'] = ""
                    if 'workstartdate' in experience:
                        temp["start_date"] = experience["workstartdate"]
                    else:
                        temp["start_date"] = ""
                    if 'workenddate' in experience:
                        temp["end_date"] = experience["workenddate"]
                    else:
                        temp["end_date"] = ""
                    if counter == 0:
                        temp["is_current_position"] = True
                        counter = counter + 1
                    else:
                        temp["is_current_position"] = False
                        counter = counter + 1
                    if 'workdescription' in experience:
                        temp["job_description"] = experience["workdescription"].strip().replace("\r\n" ,"").replace("\n","").replace("\t","")
                    else:
                        temp["job_description"] = ""

                    results['experience'].append(temp)


        # get certifications
        results['certifications'] = []
        if 'licensecertification' in people_response:
            certifications = people_response["licensecertification"]
            print("certifications : ", certifications)
            for cert in certifications:
                temp = {}
                if 'licensetype' in cert:
                    temp['certification_name'] = cert["licensetype"]
                else:
                    temp['certification_name'] = ""

                if 'licensenumber' in cert:
                    temp['licensenumber'] = cert["licensenumber"]
                else:
                    temp['licensenumber'] = ""

                if 'licensetype' in cert:
                    temp['licensetype'] = cert["licensetype"]
                else:
                    temp['licensetype'] = ""


                if 'stateissued' in cert:
                    if 'formattedvalue' in cert['stateissued']:
                        temp['stateissued'] = cert["stateissued"]["formattedvalue"]
                    else:
                        temp['stateissued'] = ""
                else:
                    temp['stateissued'] = ""

                if 'licensecertstatus' in cert:
                    if 'formattedvalue' in cert['licensecertstatus']:
                        temp['licensecertstatus'] = cert["licensecertstatus"]["formattedvalue"]
                    else:
                        temp['licensecertstatus'] = ""
                else:
                    temp['licensecertstatus'] = ""

                temp['issued_date'] = ""
                results['certifications'].append(temp)

        # get skills
        results["skills"] = []
        if 'skillset' in people_response:
            if len(people_response["skillset"]) > 0:
                for each_skill in people_response["skillset"]:
                    skill = {}
                    if 'skilllevel' in each_skill:
                        skill['skilllevel'] = each_skill["skilllevel"]
                    else:
                        skill['skilllevel'] = ""

                    if 'skill' in each_skill:
                        if 'formattedvalue' in each_skill["skill"]:
                            skill['value'] = each_skill["skill"]["formattedvalue"]
                        else:
                            skill['value'] = ""
                    else:
                        skill['value'] = ""

                    results["skills"].append(skill)


        # print("parse_results(results) : ", parse_results(results))

        return parse_results(results)
    else:
        print("error_message-----" , response["errors"][0]["errorMessage"])
        print("error_code-----", response["errors"][0]["errorCode"])


def return_bscore(score, profile_resume_id):
    score = round(score)

    update_bscore = False

    # get workflow id using profile resume id
    profile_url_data = ProfileResume.objects.filter(id=profile_resume_id).values_list("url", flat=True)[:1]
    workflow_id = profile_url_data[0].split("applicantworkflows/")[1]
    # create sanitation object
    sanitation_obj = SanitationRanking()
    sanitation_obj1 = Sanitation()

    # generate request headers
    headers = sanitation_obj.generate_request_headers()

    assessmentnotes = ""
    if score>=350 and score<=399:
        assessmentnotes = "red"
    elif score>=400 and score<=499:
        assessmentnotes = "yellow"
    elif score >=500:
        assessmentnotes= "green"

    assessmentdate = datetime.datetime.today().strftime('%Y-%m-%d %I:%M %p')

    # payload1 = "{\n    \"assessmenturl\": \"\",\n    \"assessmentresult\": \"Pass\",\n    \"assessmentscore\": 32,\n    \"assessmentdate\": \"2019-04-10 07:12 PM\",\n    \"assessmentnotes\": \"green\",\n    \"assessmentstatus\": {\n        \"id\": \"D37002019001\",\n        \"value\": \"Complete\"\n    }\n}"
    payload = "{\n    \"assessmenturl\": \"\",\n    \"assessmentresult\": \"Pass\",\n    \"assessmentscore\": " + str(score) +",\n    \"assessmentdate\": \"" + str(assessmentdate) + "\",\n    \"assessmentnotes\": \""+str(assessmentnotes)+"\",\n    \"assessmentstatus\": {\n        \"id\": \"D37002019001\",\n        \"value\": \"Complete\"\n    }\n}"
    if update_bscore == True:
        print("Inside if loop--------------------update_bscore---------------------------")
        # we are sending bscore again to icims
        # get assessment_update_url from database
        url = sanitation_obj.get_assessment_update_url(workflow_id)
        # and use PATCH request
        response = requests.request("PATCH", url, data=payload, headers=headers)
    else:
        url = "https://api.icims.com/customers/8611/applicantworkflows/" + workflow_id + "/fields/assessmentresults"
        response = requests.request("POST", url, data=payload, headers=headers)

    if response.status_code == 201:
        assessment_update_url = response.headers['Location']
        # update is_scored flag to true
        workflow_url = "https://api.icims.com/customers/8611/applicantworkflows/" + workflow_id
        sanitation_obj.update_score_flag(workflow_url , assessment_update_url)
        print("score updated---------")
        return
    elif response.status_code == 204:
        # no need to update is_scored flag since it is already updated
        print("score updated---------")
        return
    else:
        print("Error sending back bscore for workflow id - ", workflow_id)
        return
