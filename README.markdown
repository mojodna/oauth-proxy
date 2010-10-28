# OAuth Proxy

I am an OAuth proxy server. You can pass unsigned requests to me and I will
sign them using [OAuth](http://oauth.net/ "OAuth") before sending them to
their eventual destination.

At the moment, tokens and consumer keys are configurable only at start-time,
so individual proxies are limited to a single pair at a time. 2-legged OAuth
(often used in lieu of API keys) is supported by omitting `--token` and
`--token-secret` options.

## Running

Run the proxy with `twistd`:

    twistd -n oauth_proxy \
      --consumer-key <consumer key> \
      --consumer-secret <consumer secret> \
      [--token <token>] \
      [--token-secret <token secret>] \
      [-p <proxy port>] \
      [--ssl]

"." may need to be in your `PYTHONPATH` in order for this to work. You'll also
need a relatively modern version of [Twisted](http://twistedmatrix.com/
"Twisted") for this to work; OS X 10.5 comes with _2.5.0_, which is too old.
_8.2.0_ (installed via `easy_install twisted`) appears to work just fine.

If you'd like to run the proxy as a daemon, merely omit the `-n` option.

## Using

This proxy can be used with command-line tools and web browsers alike.

To use it with `curl`:

    curl -x localhost:8001 http://host.name/path

To use it with `ab` (ApacheBench):

    ab -X localhost:8001 http://host.name/path

To use it with Firefox, open the Network settings panel, under Advanced, and
set a "Manual Proxy Configuration" after clicking the "Settings..." button.
Ensure that "No Proxy for" does *not* include the host that you are attempting
to explore.

## More Information

More information on using this proxy, including instructions for obtaining
access tokens, is available in [Exploring OAuth-Protected
APIs](http://mojodna.net/2009/08/21/exploring-oauth-protected-apis.html).
