import sys
from twisted.application import internet, service
from twisted.python import usage
import oauth_proxy

class Options(usage.Options):
	synopsis = "Usage: mktap oauth_proxy --consumer_key <consumer key> --consumer_secret <consumer secret> [--token <token>] [--token_secret <token secret>] [-p <proxy port>] [--ssl] "
	longdesc = "Makes an OAuth HTTP proxy server.."
	optParameters = [
		['consumer_key', None, None, "OAuth Consumer Key"],
		['consumer_secret', None, None, "OAuth Consumer Secret"],
		['token', None, None, "OAuth Access/Request Token"],
		['token_secret', None, None, "OAuth Access/Request Token Secret"],
		['port', 'p', 8001, "Proxy port", int],
	]

	optFlags = [['ssl', 's']]

def makeService(config):
	s = service.MultiService()

	useSSL = config["ssl"]

	consumerKey = config["consumer_key"]
	consumerSecret = config["consumer_secret"]
	if config.has_key("token") and config.has_key("token_secret"):
		token = config["token"]
		tokenSecret = config["token_secret"]
	else:
		token = tokenSecret = None

	port = config["port"]

	credentials = oauth_proxy.OAuthCredentials(consumerKey, consumerSecret, token, tokenSecret)

	proxy = internet.TCPServer(port, oauth_proxy.OAuthProxyFactory(credentials, useSSL))
	proxy.setServiceParent(s)

	return s
