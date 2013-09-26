# OAuth Proxy

**NOTE**: If you're having trouble installing this, there's an [equivalent
JavaScript version
(mojodna/node-oauth-proxy)](https://github.com/mojodna/node-oauth-proxy)
that's installed via `npm install -g oauth-proxy` (once you've installed
[Node.js](http://nodejs.org/)).  It's intended to be drop-in compatible.

I am an OAuth proxy server. You can pass unsigned requests to me and I will
sign them using [OAuth](http://oauth.net/ "OAuth") before sending them to
their eventual destination.

At the moment, tokens and consumer keys are configurable only at start-time,
so individual proxies are limited to a single pair at a time. 2-legged OAuth
(often used in lieu of API keys) is supported by omitting `--token` and
`--token-secret` options.

## Installing

Install via `easy_install`:

    $ easy_install oauth-proxy

or `pip`:

    $ pip install oauth-proxy

It will automatically download and install the Python OAuth lib (`oauth`) and
Twisted (if necessary).

## Running

Run the proxy with the provided `oauth-proxy` command:

    $ oauth-proxy \
        --consumer-key <consumer key> \
        --consumer-secret <consumer secret> \
        [--token <token>] \
        [--token-secret <token secret>] \
        [-p <proxy port>] \
        [--ssl]

If you'd like to run the proxy as a daemon, run it with `twistd` directly:

    $ twistd oauth_proxy \
        --consumer-key <consumer key> \
        --consumer-secret <consumer secret> \
        [--token <token>] \
        [--token-secret <token secret>] \
        [-p <proxy port>] \
        [--ssl]

## Using

This proxy can be used with command-line tools and web browsers alike.

To use it with `curl`:

    $ curl -x localhost:8001 http://host.name/path

To use it with `ab` (ApacheBench):

    $ ab -X localhost:8001 http://host.name/path

To use it with Firefox, open the Network settings panel, under Advanced, and
set a "Manual Proxy Configuration" after clicking the "Settings..." button.
Ensure that "No Proxy for" does *not* include the host that you are attempting
to explore.

## More Information

More information on using this proxy, including instructions for obtaining
access tokens, is available in [Exploring OAuth-Protected
APIs](http://mojodna.net/2009/08/21/exploring-oauth-protected-apis.html).
