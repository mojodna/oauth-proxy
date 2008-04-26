import sys
from twisted.application import internet, service
import oauth_proxy

class Options(oauth_proxy.Options):
	pass


def makeService(config):
	s = service.MultiService()

	useSSL = config["ssl"]

	consumerKey = config["consumer-key"]
	consumerSecret = config["consumer-secret"]
	if config.has_key("token") and config.has_key("token-secret"):
		token = config["token"]
		tokenSecret = config["token-secret"]
	else:
		token = tokenSecret = None

	port = config["port"]

	credentials = oauth_proxy.OAuthCredentials(consumerKey, consumerSecret, token, tokenSecret)
	credentialProvider = oauth_proxy.StaticOAuthCredentialProvider(credentials)

	proxy = internet.TCPServer(port, oauth_proxy.OAuthProxyFactory(credentialProvider, useSSL))
	proxy.setServiceParent(s)

	return s
