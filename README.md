# enterprise-toolkit

## Introduction

The Enterprise Toolkit is a set of command-line scripts that make use of the
Google Apps Admin SDK API: https://developers.google.com/admin-sdk/. The
scripts are a good way to get introduced and experiment with the API.
They allow easy chaining of commands via simple shell scripts or more
interesting Python modules.

## Background

It is not uncommon for large enterprise customers to request the ability
to generate reports and perform actions on a domain-wide basis. The Google
Admin SDK offers many useful functions but many desirable domain-wide
operations remain to be written.

The procedures for using the Admin SDK API include many steps and usually
requires visits to a few different websites to determine all the necessary
details. These scripts are a useful start in learning how to access the
Admin SDK API for nontrivial, domain-wide operations.

Finally, many enterprise domains seek the ability to document and revoke the
3LO tokens that have been granted to third parties by domain users.  In many
cases allowing access to domain resources is a concern to domain
administrators.

Two sets of scripts are provided by the enterprise-toolkit:

* api_sample: a set of user scripts for beginners.
 * Shows OAuth2 authentication.
 * Shows use of Admin SDK Directory Users API and Google+ Domains API.
 * Shows parsing of results from API calls.
 * Shows handling errors in API calls.
 * Shows a simple implementation of argparse subcommands.
* toolkit: a set of user and token scripts for more advanced users.
 * Shows everything in api_sample (except subcommand parsing).
 * Adds generic domain-wide user reporting scripts.
 * Adds scripts to show 3LO token status and revoke tokens.
 * Shows demonstrations of resuming of interrupted long-running scripts.
 * Adds a generic approach to retrying API calls.

## Getting Started

Each set of scripts has an INSTALL document with helpful instructions for
installing the scripts.  In addition, each set of scripts includes HOWTO
documents to demonstrate a few of the commands provided.

## Support

For questions and answers join/view the
[enterprise-toolkit Google Group](https://groups.google.com/forum/#!forum/opensource-enterprise-toolkit).
