import sys
import re
import calendar
from .sanitation import Sanitation
from bs4 import BeautifulSoup
import json

cap_keys = ["first_name", "middle_name", "last_name", "company_name", "school_name", "job_title"]

def get_value(sc, value):
    # print("Inside get_value fucntion-------------")
    try:
        val = sc['resumeModel'][value]
        # print("val : ", val)
        return val
    except:
        return ''


def titlecase(s):
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), s)


def parse_results(results):
    for k, v in results.items():
        if not v:
            continue
        if k in cap_keys:
            results[k] = titlecase(v)
        if isinstance(v, str):
            results[k] = results[k].strip()
        else:
            counter = 0
            for ln in v:
                if not isinstance(ln, str):
                    for k1, v1 in ln.items():
                        if not v1:
                            continue

                        if k1 in cap_keys:
                            results[k][counter][k1] = titlecase(v1)
                        if isinstance(v1, str):
                            results[k][counter][k1] = results[k][counter][k1].strip()

                counter = counter + 1

    return results


def parse_indeed_html(data):
    print("Inside parse_indeed_html function------------")

    results = {}
    sanitation_obj = Sanitation()

    # Indeed renders a JSON dict in a script tag that contains all the information
    # we need.
    script_soup = BeautifulSoup(data, "html.parser")
    # print("script_soup : ", script_soup)
    script = None
    for el in script_soup.find_all("script"):
        if el.text.strip().startswith("window.initialState"):
            script = el
            break
    # print("script : ", script)
    if not script:
        print("Inside if loop")
        # its the other type of resume - resumes/resume1.html
        soup = BeautifulSoup(data, "html.parser")
        body = soup.find("div", {"id": "resume_body"})

        # print("body : ", body)

        # get location
        location = soup.find("p", {"id": "headline_location"}).text
        city_name, state = sanitation_obj.extract_city_and_state(location)
        if city_name != '':
            results['city'] = city_name
            results['state_code'] = state.state_code if state else None

        # get basic Information
        info = soup.find("h1", {"id": "resume-contact"}).text
        info = info.split()
        if len(info) == 3:
            results['first_name'] = info[0]
            results['middle_name'] = info[1]
            results['last_name'] = info[2]
        elif len(info) == 2:
            results['first_name'] = info[0]
            results['middle_name'] = info[1]
        elif len(info) == 1:
            results['first_name'] = info[0]

        # get summary
        try:
            results['summary'] = soup.find("p", {"id": "res_summary"}).text
        except:
            pass

        # get education
        results['education'] = []
        educations = soup.find_all("div", {"class": "education-section"})
        for education in educations:
            temp = {}
            try:
                temp['degree_name'] = education.find("p", {"class": "edu_title"}).text.strip()

                temp['degree_type'] = sanitation_obj.guess_degree_type(temp['degree_name'])
                temp['degree_major'] = temp['degree_name']
            except:
                pass
            try:
                major, typ = sanitation_obj.extract_degree_info(temp['degree_name'])
                temp['degree_type'] = typ
                temp['degree_major'] = major
            except:
                print("Inside exception--------------")
                pass
            try:
                edu_school = education.find("div", {"class": "edu_school"}).text
                if '-' in edu_school:
                    school_name = edu_school.split("-")
                    temp['school_name'] = school_name[0]
                else:
                    temp['school_name'] = edu_school
            except:
                pass
            try:
                location = education.find("div", {"class": "inline-block"}).text
                city_name, state = sanitation_obj.extract_city_and_state(location)
                temp['city_name'] = city_name
                temp['state_code'] = state.state_code if state else None
            except:
                pass
            try:
                edu_dates = education.find("p", {"class": "edu_dates"}).text.split(' to ')
                temp['start_date'] = sanitation_obj.extract_date(edu_dates[0], False)
                temp['degree_date'] = sanitation_obj.extract_date(edu_dates[-1], False)
                temp['end_date'] = sanitation_obj.extract_date(edu_dates[-1], False)
            except:
                pass
            results['education'].append(temp)

        # get additional_information
        information = soup.find_all("div", {"class": "section-item additionalInfo-content"})
        if len(information) > 0:
            try:
                results['additional_information'] = information[0].find(
                    "div", {"class": "data_display"}).text
            except:
                pass
        else:
            pass

        # get skills
        results["skills"] = []
        skills = soup.find_all("div", {"class": "section-item skills-content"})
        if len(skills) > 0:
            try:
                skills_container = skills[0].find(
                    "div", {"class": "skill-container resume-element"})
                all_skills = skills_container.find_all("span", {"class": "skill-text"})
                for each_skill in all_skills:
                    results["skills"].append(each_skill.text)
            except:
                pass
        else:
            pass

        # get groups
        results["groups"] = []
        groups = soup.find_all("div", {"class": "section-item groups-content"})
        if len(groups) > 0:
            try:
                grp_items = groups[0].find_all("div", {"id": "group-items"})
                grps_container = grp_items[0].find_all(
                    "div", {"class": "data_display"})
                if len(grps_container) > 0:
                    for each_container in grps_container:
                        grps = {}
                        grps["group_title"] = each_container.find(
                            "p", {"class": "group_title"}).text
                        grps["group_date"] = each_container.find("p", {"class": "group_date"}).text
                        results["groups"].append(grps)
                else:
                    pass
            except:
                pass
        else:
            pass

        # get awards
        results["awards"] = []
        awards = soup.find_all("div", {"class": "section-item awards-content"})
        if len(awards) > 0:
            try:
                award_items = awards[0].find_all("div", {"id": "award-items"})
                awards_container = award_items[0].find_all(
                    "div", {"class": "data_display"})
                if len(awards_container) > 0:
                    for each_container in awards_container:
                        awards = {}
                        awards["award_title"] = each_container.find(
                            "p", {"class": "award_title"}).text
                        awards["award_date"] = each_container.find(
                            "p", {"class": "award_date"}).text
                        awards["award_description"] = each_container.find(
                            "p", {"class": "award_description"}).text
                        results["awards"].append(awards)
                else:
                    pass
            except:
                pass
        else:
            results['awards'] = []

        # get experience
        results['experience'] = []
        experiences = soup.find_all("div", {"class": "work-experience-section"})
        for experience in experiences:
            temp = {}
            try:
                temp['job_title'] = experience.find("p", {"class": "work_title"}).text
            except:
                pass
            try:
                c_name = experience.find("div", {"class": "work_company"}).text.split('-')
                temp['company_name'] = c_name[0]
                city_name, state = sanitation_obj.extract_city_and_state(c_name[1])
                temp['city_name'] = city_name
                temp['state_code'] = state.state_code if state else None
            except:
                pass
            try:
                work_dates = experience.find("p", {"class": "work_dates"}).text.split(' to ')
                temp['start_date'] = sanitation_obj.extract_date(work_dates[0], False)
                if 'Present' in work_dates[-1]:
                    temp['is_current_position'] = 'True'
                else:
                    temp['is_current_position'] = 'False'
                    temp['end_date'] = sanitation_obj.extract_date(work_dates[-1], False)
            except:
                pass
            try:
                temp['job_description'] = experience.find(
                    "p", {"class": "work_description"}).text.replace('\\u2022', '').replace('\u00a0', '').replace('\n', '').replace(' \u2022', '')
            except:
                pass
            results['experience'].append(temp)

        # get certifications
        results['certifications'] = []
        certifications = soup.find_all("div", {"class", "certification-content"})
        for cert in certifications:
            temp = {}
            try:
                temp['certification_name'] = cert.find("p", {"class": "certification_title"}).text
            except:
                pass
            try:
                cert_dates = cert.find("p", {"class": "certification_date"}).text.split(' to ')
                temp['issued_date'] = sanitation_obj.extract_date(cert_dates[0], False)
            except:
                pass
            results['certifications'].append(temp)
        return parse_results(results)
    else:
        print("Inside else loop------------")
        s = script.text.strip().replace('window.initialState = JSON.parse(\'', '')[:-3]
        # print("s before : ", s)
        s = s.encode('utf-8').decode('unicode_escape').encode('latin-1')
        # print("s : ", s)

        s = str(s, 'utf-8')
        sc = json.loads(s)
        # print("sc : ", sc)
        # get certifications
        results['certifications'] = get_value(sc, 'certifications')
        # print("results['certifications'] : ", results['certifications'])

        # get location
        location = get_value(sc, 'location')
        loc_parsed = sanitation_obj.extract_city_and_state(location)
        if loc_parsed:
            city_name, state = loc_parsed
            results['city'] = city_name or None
            results['state_code'] = state.state_code if state else None

        # get education
        results['education'] = get_value(sc, 'education')
        var_edu = ["city_name", "degree_date", "degree_major", "degree_name", "degree_type",
                   "end_date", "school_name", "school_type", "start_date", "state_code"]
        for i in results['education']:
            if 'dateRange' in i.keys():
                if i['dateRange']:
                    edu_dates = i['dateRange'].split(' to ')
                    i.update({'degree_date': sanitation_obj.extract_date(edu_dates[-1], False)})
                    i.update({'end_date': sanitation_obj.extract_date(edu_dates[-1], False)})
                    edu_dates.pop(-1)
                    i.update({'start_date': sanitation_obj.extract_date(
                        edu_dates[0], False) if edu_dates else ''})
                i.pop('dateRange', None)
            if 'location' in i.keys():
                loc = i['location']
                if loc:
                    city_name, state = sanitation_obj.extract_city_and_state(loc)
                    i.update({'city_name': city_name or None})
                    i.update({'state_code': state.state_code if state else None})
                i.pop('location', None)
            if 'degree' in i.keys():
                i.update({'degree_name': i['degree']})
                i.update({'degree_type': sanitation_obj.guess_degree_type(i['degree'])})
                i.update({'degree_major': i['field']})
                i.pop('degree', None)
            if 'field' in i.keys():
                i.update({'degree_major': i['field']})
                i.pop('field', None)
            if 'university' in i.keys():
                i.update({'school_name': i['university']})
                i.pop('university', None)
            if 'id' in i.keys():
                i.pop('id', None)

        # get experience
        results['experience'] = get_value(sc, 'workExperience')
        var_exp = ["city_name", "company_name", "end_date", "is_current_position",
                   "job_description", "job_title", "start_date", "state_code"]
        for i in results['experience']:
            if 'company' in i.keys():
                i.update({'company_name': i['company'] or None})
                i.pop('company', None)
            if 'dateRange' in i.keys():
                exp_dates = i['dateRange'].split(' to ')
                i.update({'start_date': sanitation_obj.extract_date(exp_dates[0], False)})
                if 'Present' in exp_dates[-1]:
                    i.update({'is_current_position': True})
                else:
                    i.update({'is_current_position': False})
                    i.update({'degree_date': sanitation_obj.extract_date(exp_dates[-1], False)})
                    i.update({'end_date': sanitation_obj.extract_date(exp_dates[-1], False)})
                i.pop('dateRange', None)
            if 'description' in i.keys():
                i.update({'job_description': i['description'].replace('\\n', ' ').replace(
                    '\u2751', '').replace('\u2022', '').replace('\\t', ' ').replace('\n', ' ')})
                i.pop('description', None)
            if 'title' in i.keys():
                i.update({'job_title': i['title'] or None})
                i.pop('title', None)
            if 'location' in i.keys():
                loc = i['location']
                if loc:
                    city_name, state = sanitation_obj.extract_city_and_state(loc)
                    i.update({'city_name': city_name})
                    i.update({'state_code': state.state_code if state else None})
                i.pop('location', None)
            if 'id' in i.keys():
                i.pop('id', None)

        # added skills
        results['skills'] = [skl['skill'] for skl in get_value(sc, 'skills')]

        soup = BeautifulSoup(data, 'html.parser')
        elem = soup(text='Additional Information', limit=1)
        if elem:
            bsaddn = elem[0].parent.parent.select_one('div.rezemp-ResumeDisplaySection-content')
            addn = str(bsaddn).replace('<br/>', ' ')
            bsaddn = BeautifulSoup(addn, 'html.parser')
            results['additional_information'] = bsaddn.get_text()

        for i in results['certifications']:
            if 'displayDate' in i.keys():
                if i['displayDate']:
                    edu_dates = i['displayDate'].split(' to ')
                    i.update({'start_date': sanitation_obj.extract_date(edu_dates[0], False)})
                    i.update({'end_date': sanitation_obj.extract_date(edu_dates[-1], False)})
                i.pop('displayDate', None)
            if 'id' in i.keys():
                i.pop('id', None)

        results['summary'] = get_value(sc, 'summary').replace('\\n', ' ')
        results['first_name'] = get_value(sc, 'firstName')
        results['last_name'] = get_value(sc, 'fullName').replace(results['first_name'], '')
        results['middle_name'] = get_value(sc, 'middleName')

        results['email_addresses'] = []
        email_address = get_value(sc, 'email')
        if email_address:
            results['email_addresses'].append(email_address)

        results['phones'] = []
        phone_number = sanitation_obj.prepare_phn_number(get_value(sc, 'phoneNumber'))
        if phone_number:
            results['phones'].append(phone_number)

        return parse_results(results)
