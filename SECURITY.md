# Security Policy

## Scope

This repository contains the RepoAura prompt and related documentation. It does not contain a standalone runtime or a guarantee that AI-host security controls are enforced.

Security reports may concern unsafe prompt guidance, unintended disclosure encouraged by repository documentation, or vulnerabilities in files maintained here. Reports about a target repository generated using RepoAura should identify that target separately; do not include private source content unless its owner has authorized disclosure.

## Supported versions

Only the latest version of the prompt in the default branch is considered for security fixes. Older copies may not receive updates.

## Reporting a vulnerability

Please do not report vulnerabilities in a public issue.

If GitHub's **Report a vulnerability** option is enabled for this repository, use it. Otherwise, contact the repository owner privately through GitHub's profile or another contact channel they have explicitly published. If no private route is available, do not disclose sensitive details publicly.

Include a concise description, affected file/version, impact, and safe reproduction details. Do not include live credentials, private user data, or third-party repository contents. The maintainers will acknowledge and coordinate a response where possible; no response or remediation timeframe is guaranteed.

## Security limitations

RepoAura is a prompt-driven workflow. Prompt instructions do not, by themselves, intercept model requests, block tools, scan all context, or enforce permissions. Any host hooks, gateways, or repository controls must be configured and tested independently in the environment where they are used.
