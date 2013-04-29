## Implementation of an OAuth HTTP proxy
# Adapted from Example 4-8, Twisted Network Programming Essentials by Abe Fettig. Copyright 2005 O'Reilly & Associates.
# Adapted by Seth Fitzsimmons <seth@mojodna.net>

## TODO
# - provide a way of specifying access tokens (and possibly secrets, if not handled via lookup) - Basic Auth?

import cgi
from oauth import oauth
import sgmllib, re, urlparse
import sys

# don't include SSL if it's not installed
try:
  from twisted.internet import ssl
except ImportError:
  pass

from twisted.web import proxy, http
from twisted.python import log, usage
from zope.interface import implements, Interface

class IOAuthCredentialProvider(Interface):
	"""An OAuth credential provider"""

	def fetchCredentials():
		"""Fetch credentials"""


class StaticOAuthCredentialProvider:
	implements(IOAuthCredentialProvider)

	def __init__(self, credentials):
		self.credentials = credentials

	def fetchCredentials(self):
		return self.credentials


class OAuthCredentials:
	"""
	A container for OAuth credentials
	"""
	def __init__(self, consumerKey, consumerSecret, token = None, tokenSecret = None, signatureMethod = oauth.OAuthSignatureMethod_HMAC_SHA1()):
		self.oauthConsumer = oauth.OAuthConsumer(consumerKey, consumerSecret)

		if token is not None and tokenSecret is not None:
			self.oauthToken = oauth.OAuthToken(token, tokenSecret)
		else:
			self.oauthToken = None

		self.signatureMethod = signatureMethod


class Options(usage.Options):
	synopsis = "--consumer-key <consumer key> --consumer-secret <consumer secret> [--token <token>] [--token-secret <token secret>] [-p <proxy port>] [--ssl]"
	longdesc = "An OAuth HTTP proxy server."
	optParameters = [
		['consumer-key', None, None, "OAuth Consumer Key"],
		['consumer-secret', None, None, "OAuth Consumer Secret"],
		['token', None, None, "OAuth Access/Request Token"],
		['token-secret', None, None, "OAuth Access/Request Token Secret"],
		['port', 'p', 8001, "Proxy port"],
	]

	optFlags = [['ssl', 's']]

        def postOptions(self):
            if self['consumer-key'] is None or self['consumer-secret'] is None:
                raise usage.UsageError, "Your consumer key and secret must be provided."


class OAuthProxyClient(proxy.ProxyClient):
	def connectionMade(self):
		# if retrieval of OAuth credentials is to be asynchronous, it needs to be done here (if it's even possible)
		# otherwise, this class has no point
		# however, it's possible that reading headers can't happen in OAuthProxyClientFactory
		proxy.ProxyClient.connectionMade(self)


class OAuthProxyClientFactory(proxy.ProxyClientFactory):
	def buildProtocol(self, addr):
		credentials = self.father.credentialProvider.fetchCredentials()
		oauthRequest = self.signRequest(credentials)

		client = proxy.ProxyClientFactory.buildProtocol(self, addr)
		# upgrade proxy.proxyClient object to OAuthProxyClient
		client.__class__ = OAuthProxyClient
		client.factory = self

		client.headers.update(oauthRequest.to_header())
		return client

	def signRequest(self, credentials):
		"""Create an OAuthRequest and sign it"""

		if self.father.useSSL:
			path = self.father.path.replace("http", "https", 1)
		else:
			path = self.father.path

		# python parses arguments into a dict of arrays, e.g. 'q=foo' becomes {'q': ['foo']}
		# while from_consumer_and_token expects a dict of strings, so we cross our fingers,
		# hope there are no repeated arguments ('q=foo&q=bar'), and take the last value of
		# each array.
		args = dict((k,v[-1]) for k,v in self.father.args.items())

		# create an OAuth Request from the pieces that we've assembled
		oauthRequest = oauth.OAuthRequest.from_consumer_and_token(
			oauth_consumer=credentials.oauthConsumer,
			token=credentials.oauthToken,
			http_method=self.father.method,
			http_url=path,
			parameters=args,
		)

		# now, sign it
		oauthRequest.sign_request(credentials.signatureMethod, credentials.oauthConsumer, credentials.oauthToken)

		# TODO add X-Forwarded-For headers

		return oauthRequest


class OAuthProxyRequest(proxy.ProxyRequest):
	protocols = {'http': OAuthProxyClientFactory}

	def __init__(self, credentialProvider, useSSL, *args):
		self.credentialProvider = credentialProvider
		self.useSSL = useSSL
		proxy.ProxyRequest.__init__(self, *args)

		if self.useSSL:
			# Since we magically mapped HTTP to HTTPS, we want to make sure that the transport knows as much
			self._forceSSL = True
			self.ports["http"] = 443

	# Copied from proxy.ProxyRequest just so the reactor connection can be SSL
	def process(self):
		headers = self.getAllHeaders().copy()
		if self.uri.startswith('/'):
			self.uri = 'http://' + headers['host'] + self.uri
			self.path = self.uri
		parsed = urlparse.urlparse(self.uri)
		protocol = parsed[0]
		host = parsed[1]
		port = self.ports[protocol]
		if ':' in host:
			host, port = host.split(':')
			port = int(port)
		rest = urlparse.urlunparse(('', '') + parsed[2:])
		if not rest:
			rest = rest + '/'
		class_ = self.protocols[protocol]
		if 'host' not in headers:
			headers['host'] = host
		self.content.seek(0, 0)
		s = self.content.read()
		clientFactory = class_(self.method, rest, self.clientproto, headers,
							   s, self)
		# The magic line for SSL support!
		if self.useSSL:
			self.reactor.connectSSL(host, port, clientFactory, ssl.ClientContextFactory())
		else:
			self.reactor.connectTCP(host, port, clientFactory)


class OAuthProxy(proxy.Proxy):
	def __init__(self, credentialProvider, useSSL):
		self.credentialProvider = credentialProvider
		self.useSSL = useSSL
		proxy.Proxy.__init__(self)

	def requestFactory(self, *args):
		return OAuthProxyRequest(self.credentialProvider, self.useSSL, *args)


class OAuthProxyFactory(http.HTTPFactory):
	def __init__(self, credentialProvider, useSSL):
		self.credentialProvider = credentialProvider
		self.useSSL = useSSL
		http.HTTPFactory.__init__(self)

	def buildProtocol(self, addr):
		protocol = OAuthProxy(self.credentialProvider, self.useSSL)
		return protocol
