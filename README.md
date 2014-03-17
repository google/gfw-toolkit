# enterprise-toolkit

## Introduction

The Enterprise Toolkit is a set of command-line scripts that make use of the
Google Apps Admin SDK API: https://developers.google.com/admin-sdk/. The
scripts are a good way to get introduced and experiment with the API.
They allow easy chaining of commands via simple shell scripts or more
interesting Python modules.

## Background

It is also not uncommon for large enterprise customers to request the ability
to perform actions on a domain-wide basis.  Many large enterprise domains
desire the ability to offer more detailed reporting of user information than
is currently provided by the admin console.  These scripts provide an initial
framework for simple custom reporting of domain user and Google+ profile
information.

Another domain-wide example would be the ability to document the 3LO tokens
that have been granted to third parties by domain users. In many cases
allowing access to domain resources is a concern to domain administrators.
These scripts provide an initial framework for examining and reporting token
status on a domain-wide basis.

Finally, the procedure for using the Admin SDK API is a multi-step exercise
usually requiring visits to a few different websites to exactly address
each given domains needs. These scripts are useful in automating and
documenting the steps for some non-trivial automated access to Google Apps APIs.

## Objectives

* Allow large domain customers to easily review and revoke 3LO tokens issued by
their domain users in an automated way.
* Establish a foundation of automated tools for domain-wide user reporting.
* Allow long-running commands to be resumable.
* Produce detailed log output for domain token commands to be reviewable.
* Demonstrate reliable access against the Google API surface
(e.g including error handling, logging, unit testing and backoff).

## Authentication

Users will be authenticated by registering a ‘native’ app with the Google
Developers Console.  As part of this process a ‘client_secrets.json’ file
will be downloaded which includes a ‘client_secret’ which is used to obtain
an access token.

The tools will use the google-api-python-client libraries to consume the
client_secrets.json file and obtain the active access_token.  The tools will
persist this token in a local file and re-use it.  The google-api-python-client libraries make this easy.

The Admin SDK requires the user to be a domain Admin.

## Commands

Initially - run once

 Command               | Description
:----------------------|:------------------------------------------------------
 set_default_domain.py | Save default domain for subsequent commands.

Simple Domain/User Interrogation

 Command          | Description
:-----------------|:-----------------------------------------------------------
ls_customer_id.py | Show unique Google customer id.
ls_user.py        | Show details about one user.  Allows a -p option to show
                    Google+ profile details about one user.
ls_users.py       | Show simple or detailed list about domain users.

Modify Users

 Command          | Description
:-----------------|:-----------------------------------------------------------
add_user.py       | Add/modify domain user.
rm_user.py        | Remove domain user.

User Reporting

 Command                     | Description
:----------------------------|:------------------------------------------------
report_users.py              | Summarize domain users and metadata.
report_plus_domains_users.py | Use the Plus API to enumerate users.
report_org_counts.py         | Count domain users in orgs.

Simple Token Interrogation

 Command                       | Description
:------------------------------|:----------------------------------------------
ls_tokens_for_user.py          | Show tokens granted by one user.
ls_tokens_for_user_clientid.py | Show if tokens granted by one user to one
                                 domain.

Domain Wide Token Interrogation

 Command                       | Description
:------------------------------|:----------------------------------------------
gather_domain_token_stats.py   | Gather a local cache of token status for an
                                 entire domain.
report_domain_token_status.py  | Show a summary of the domain token information.

Simple Token Revocation

 Command                           | Description
:----------------------------------|:------------------------------------------
revoke_tokens_for_user_clientid.py | Revoke any tokens one user has authorized
                                     to one third party.


Domain Wide Token Revocation

 Command                             | Description
:------------------------------------|:----------------------------------------
revoke_tokens_for_domain_clientid.py | Revoke any tokens any user has
                                       authorized to one third party.
revoke_unapproved_tokens.py          | Automated, logging command to revoke
                                       domain tokens using a black list.

