#!/usr/bin/env python

## Implementation of an OAuth HTTP proxy
# Adapted from Example 4-8, Twisted Network Programming Essentials by Abe Fettig. Copyright 2005 O'Reilly & Associates.
# Adapted by Seth Fitzsimmons <seth@mojodna.net>

## TODO
# - provide a way of specifying access tokens (and possibly secrets, if not handled via lookup) - Basic Auth?

import cgi
from oauth import oauth
import sgmllib, re, urlparse
import sys
from twisted.internet import ssl
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


class OAuthProxyClient(proxy.ProxyClient):
	def connectionMade(self):
		# if retrieval of OAuth credentials is to be asynchronous, it needs to be done here (if it's even possible)
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
		
		# extract GET params into a list
		if self.father.uri.find("?") > 0:
			params = cgi.parse_qs(self.father.uri.split('?', 1)[1], keep_blank_values = False)
		else:
			params = {}

		if self.father.useSSL:
			path = self.father.path.replace("http", "https", 1)
		else:
			path = self.father.path

		# create an OAuth Request from the pieces that we've assembled
		oauthRequest = oauth.OAuthRequest.from_consumer_and_token(
			credentials.oauthConsumer,
			credentials.oauthToken,
			self.father.method,
			path,
			params
		)
		# now, sign it
		oauthRequest.sign_request(credentials.signatureMethod, credentials.oauthConsumer, credentials.oauthToken)
	    
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
		headers = self.getAllHeaders().copy()
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
