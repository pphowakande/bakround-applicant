class Networking {
    /*
        Generic networking function for performing JSON HTTP requests.
    */
    static json(method, path, params = null) {
        let opts  = {
              method: method,
              credentials: "same-origin",
              redirect: "follow",
              headers: {
                  "Content-Type": "application/json",
                  "Accept": "application/json",
                  "X-CSRFToken": window.csrf_token
              }
        };
        
        let url = path;
        if (params) {
            if (method == "GET") {
                url += "?" + Object.entries(params)
                                   .map(([k, v]) => encodeURIComponent(k) + "=" + encodeURIComponent(v))
                                   .join("&");
            } else {
                opts.body = JSON.stringify(params);
            }
        }

        return fetch(url, opts).then(res =>
            res.text().then(text => {
                let obj = text.length === 0 ? null : JSON.parse(text);
                if (res.ok) return obj;
                let err = new Error((obj ? obj.error : "Unknown Error") || res.statusText);
                err.responseBody = obj;
                err.responseCode = res.status;
                throw err;
            })
        );
    }

    /* Common Requests */

    static getClosability(profileIds, employerJobId) {
        return Networking.json("POST", "/employer/closeability_metric", {
            profile_ids: profileIds,
            employer_job_id: employerJobId
        });
    }

    static addToJob(employerJobId, profileIds, contact=true) {
        if (!Array.isArray(profileIds)) {
            profileIds = [profileIds];
        }
        return Networking.json("POST", "/employer/add_candidate_to_job", {
            employer_job_id: employerJobId,
            profile_ids: profileIds,
            contact: contact
        });
    }

    static getContactInfo(candidateId) {
        return Networking.json("POST", `/employer/contact_info/${candidateId}`);
    }
};

export default Networking;
