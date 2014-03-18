# enterprise-toolkit/api_sample

## Introduction

This is a simple example solution demonstrating the user parts of the
Admin SDK API and Google+ Domains API.

The solution includes Python code examples of:
-authenticating using OAuth2
-using Google's discoverable APIs (https://developers.google.com/discovery/)
-parsing results from API calls
-handling errors from API calls

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
documents to demonstrated a few of the commands provided.

## Support

For questions and answers join/view the
[enterprise-toolkit Google Group](https://groups.google.com/forum/#!forum/opensource-enterprise-toolkit).
