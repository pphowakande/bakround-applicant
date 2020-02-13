# Verifier

This code powers the verifyingservice.

## Verification

Verification is the process of "filling in the gaps" in a Profile. We rescrape
using a paid indeed account (risky, but this minimizes risk since it's selective),
and we query external reverse lookup services.

First, let's define some terms:

Name Verification: The process through which a real name is obtained for a Profile.
                   a. You must set the `name_verification_completed` attr to `True`
                   b. The new name must have at least a first and last name
                   c. The new name must not be the old name
Contact Information Verification: The process through which contact information is obtained for a profile.
                                  The profile needn't necessarily have undergone Name Verification, but
                                  some means of CIV require it.
External Contact: The process through which a Profile is contacted through the second party (i.e. the site
                  we scraped their profile from), and we watch for email messages that are responses if necessary.
                  This is a last ditch attempt to collect the data.

As you can see, getting non-anonymous data is a challenge, and usually risky. This necessitates doing the
risky business as infrequently as humanly (or, rather, computationally) possible.

## Steps of Verification

1. Name Verification. This is an invariant.
2. Contact Information Verification. If we have a name (99% of the time), we can use this.
       PIPL is a very unreliable lookup broker right now, and needs some TLC.
3. External Contact: We used to have an outsource worker doing this, which was anything but ideal.
                     We only use it if we can't get the deets on a profile sooner.

## Notes about legacy

Emails and phone numbers used to be stored in two places (the previous developer's design):

     a. the Profile record (profile.{email,phone})
     b. The ProfileExternalData record
     c. NotificationBouncedEmail contains all bounced emails
     d. Another Notification* model whose name eludes me

We have a function (in ./utils.py) that will collect all this information. Use it before working with
contact information. (`collect_contact_info_for_profile(profile_id)`)

## Notes for querying Pipl, Whitepages, etc:

- If a location doesn't exist for a profile, use the location of the most recent job
- Do NOT use ProfileExternalData records. Use ProfileEmail and ProfilePhoneNumber
- Should we save the response? It does cost money.

Ultimately, verification collects as much data as possible from the database and makes
sure it's valid. We're scraping data after all; the quality of the data is going to be poor.