# Security policy

## Supported versions

Only the latest release and `main` receive fixes.

## Reporting a vulnerability

Do not open a public issue. Use GitHub's private reporting: the **Security** tab of this repository, then **Report a vulnerability**.

Include what you found, how to reproduce it, and what it affects. You should get a reply within seven days.

## What matters most here

- Anything that lets a device be driven without a Hardware Lane Grant.
- Anything that lets a malformed frame or stream do something other than fail closed.
- Anything that breaks the link between an Output Stream's identifier and its content.
