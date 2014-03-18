# enterprise-toolkit/toolkit

## Introduction

This is an example solution demonstrating the user parts of the
Admin SDK API and Google+ Domains API.

The solution includes Python code examples of:
-authenticating using OAuth2
-using Google's discoverable APIs (https://developers.google.com/discovery/)
-parsing results from API calls
-handling errors from API calls
-retrying API calls due to per-second quota responses

The solution is divided between 4 main directories:
-admin_sdk_directory_api: code to wrap admin_sdk api supported.
-cmds: command line wrappers that invoke the api wrappers for easy use/testing.
-plus_domains_api: code to wrap plus_domains api supported.
-utils: helper code that is used commonly used across cmds.

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

## Getting Started

Each set of scripts has an INSTALL document with helpful instructions for
installing the scripts.  In addition, each set of scripts includes HOWTO
documents to demonstrate a few of the commands provided.

## Commands

### Initially - run once

 Command               | Description
:----------------------|:------------------------------------------------------
 set_default_domain.py | Save default domain for subsequent commands.

### Simple Domain/User Interrogation

 Command          | Description
:-----------------|:-----------------------------------------------------------
ls_customer_id.py | Show unique Google customer id.
ls_user.py        | Show details about one user.  Allows a -p option to show Google+ profile details about one user.
ls_users.py       | Show simple or detailed list about domain users.

### Modify Users

 Command          | Description
:-----------------|:-----------------------------------------------------------
add_user.py       | Add/modify domain user.
rm_user.py        | Remove domain user.

### User Reporting

 Command                     | Description
:----------------------------|:------------------------------------------------
report_users.py              | Summarize domain users and metadata.
report_plus_domains_users.py | Use the Plus API to enumerate users.
report_org_counts.py         | Count domain users in orgs.

### Simple Token Interrogation

 Command                       | Description
:------------------------------|:----------------------------------------------
ls_tokens_for_user.py          | Show tokens granted by one user.
ls_tokens_for_user_clientid.py | Show if tokens granted by one user to one domain.

### Domain Wide Token Interrogation

 Command                       | Description
:------------------------------|:----------------------------------------------
gather_domain_token_stats.py   | Gather a local cache of token status for an entire domain.
report_domain_token_status.py  | Show a summary of the domain token information.

### Simple Token Revocation

 Command                           | Description
:----------------------------------|:------------------------------------------
revoke_tokens_for_user_clientid.py | Revoke any tokens one user has authorized to one third party.


### Domain Wide Token Revocation

 Command                             | Description
:------------------------------------|:----------------------------------------
revoke_tokens_for_domain_clientid.py | Revoke any tokens any user has authorized to one third party.
revoke_unapproved_tokens.py          | Automated, logging command to revoke domain tokens using a black list.

## Support

For questions and answers join/view the
[enterprise-toolkit Google Group](https://groups.google.com/forum/#!forum/opensource-enterprise-toolkit).
