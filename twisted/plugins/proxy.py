from zope.interface import implements

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
        # TODO add error handling for missing params
        
		useSSL = options["ssl"]

		consumerKey = options["consumer-key"]
		consumerSecret = options["consumer-secret"]
		if options.has_key("token") and options.has_key("token-secret"):
			token = options["token"]
			tokenSecret = options["token-secret"]
		else:
			token = tokenSecret = None

		port = int(options["port"])

		credentials = oauth_proxy.OAuthCredentials(consumerKey, consumerSecret, token, tokenSecret)
		credentialProvider = oauth_proxy.StaticOAuthCredentialProvider(credentials)

		return internet.TCPServer(port, oauth_proxy.OAuthProxyFactory(credentialProvider, useSSL))


serviceMaker = OAuthProxyServiceMaker()
