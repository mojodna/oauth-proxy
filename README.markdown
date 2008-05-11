# OAuth Reverse Proxy

I am an OAuth proxy server.  You can pass unsigned requests to me and I will sign them using [OAuth](http://oauth.net/ "OAuth") before sending them to their eventual destination.

At the moment, tokens and consumer keys are configurable only at start-time, so individual proxies are limited to a single pair at a time.


## Running

Provided that "." is in your `PYTHONPATH`, you should be able to run the proxy with `twistd`:

    twistd -n oauth_proxy --consumer-key <consumer key> --consumer-secret <consumer secret> [--token <token>] [--token-secret <token secret>] [-p <proxy port>] [--ssl]


## Running as a daemon

You may run the proxy with `twistd` directly (omitting the _-n_ argument) or you may generate a pre-configured tap, which can then be packaged and distributed.  To generate a tap:

    mktap oauth_proxy --consumer-key <consumer key> --consumer-secret <consumer secret> [--token <token>] [--token-secret <token secret>] [-p <proxy port>] [--ssl]

To run the tap (using the settings that were provided when creating it):

    twistd -f oauth_proxy.tap
