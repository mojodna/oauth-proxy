from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet

from oauth_proxy import oauth_proxy

class OAuthProxyServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "oauth_proxy"
    description = "OAuth HTTP proxy"
    options = oauth_proxy.Options

    def makeService(self, options):
		useSSL = options["ssl"]

		consumerKey = options["consumer_key"]
		consumerSecret = options["consumer_secret"]
		if options.has_key("token") and options.has_key("token_secret"):
			token = options["token"]
			tokenSecret = options["token_secret"]
		else:
			token = tokenSecret = None

		port = options["port"]

		credentials = oauth_proxy.OAuthCredentials(consumerKey, consumerSecret, token, tokenSecret)
		credentialProvider = oauth_proxy.StaticOAuthCredentialProvider(credentials)

		return internet.TCPServer(port, oauth_proxy.OAuthProxyFactory(credentialProvider, useSSL))


serviceMaker = OAuthProxyServiceMaker()