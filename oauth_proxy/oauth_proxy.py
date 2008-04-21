#!/usr/bin/env python

## Implementation of an OAuth HTTP proxy
# Adapted from Example 4-8, Twisted Network Programming Essentials by Abe Fettig. Copyright 2005 O'Reilly & Associates.
# Adapted by Seth Fitzsimmons <seth@mojodna.net>

## TODO
# - provide a way of specifying access tokens (and possibly secrets, if not handled via lookup) - Basic Auth?

import sgmllib, re, urlparse
from twisted.internet import ssl
from twisted.web import proxy, http
import sys
from twisted.python import log
from oauth import oauth
import cgi

# Container for OAuth credentials
class OAuthCredentials:
	def __init__(self, consumerKey, consumerSecret, accessToken = None, accessTokenSecret = None, signatureMethod = oauth.OAuthSignatureMethod_HMAC_SHA1()):
		self.oauthConsumer = oauth.OAuthConsumer(consumerKey, consumerSecret)
		
		if accessToken is not None and accessTokenSecret is not None:
			self.oauthToken = oauth.OAuthToken(accessToken, accessTokenSecret)
		else:
			self.oauthToken = None
			
		self.signatureMethod = signatureMethod


class OAuthProxyClient(proxy.ProxyClient):
	def connectionMade(self):
		# this is where we make the donuts
		
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
			self.father.oauthCredentials.oauthConsumer,
			self.father.oauthCredentials.oauthToken,
			self.father.method,
			path,
			params
		)
		# now, sign it
		oauthRequest.sign_request(self.father.oauthCredentials.signatureMethod, self.father.oauthCredentials.oauthConsumer, self.father.oauthCredentials.oauthToken)
	    
		self.headers.update(oauthRequest.to_header())
		print "Header: ", self.headers["Authorization"]
		
		proxy.ProxyClient.connectionMade(self)


class OAuthProxyClientFactory(proxy.ProxyClientFactory):
	def buildProtocol(self, addr):
		client = proxy.ProxyClientFactory.buildProtocol(self, addr)
		# upgrade proxy.proxyClient object to OAuthProxyClient
		client.__class__ = OAuthProxyClient
		return client


class OAuthProxyRequest(proxy.ProxyRequest):
	protocols = {'http': OAuthProxyClientFactory}
	# if USE_SSL:
	# 	# Yes, this is correct; we want to map HTTP requests to HTTPS requests
	# 	ports = {'http': 443}

	def __init__(self, oauthCredentials, useSSL, *args):
		self.oauthCredentials = oauthCredentials
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
	def __init__(self, oauthCredentials, useSSL):
		self.oauthCredentials = oauthCredentials
		self.useSSL = useSSL
		proxy.Proxy.__init__(self)

	def requestFactory(self, *args):
		return OAuthProxyRequest(self.oauthCredentials, self.useSSL, *args)


class OAuthProxyFactory(http.HTTPFactory):
	def __init__(self, oauthCredentials, useSSL):
		self.oauthCredentials = oauthCredentials
		self.useSSL = useSSL
		http.HTTPFactory.__init__(self)

	def buildProtocol(self, addr):
		protocol = OAuthProxy(self.oauthCredentials, self.useSSL)
		return protocol


if __name__ == "__main__":
	from twisted.internet import reactor
	consumerKey = "consumer key"
	consumerSecret = "consumer secret"
	accessToken = "access token"
	accessTokenSecret = "access token secret"

	credentials = OAuthCredentials(consumerKey, consumerSecret, accessToken, accessTokenSecret)
	prox = OAuthProxyFactory(credentials, False)
	reactor.listenTCP(PROXY_PORT, prox)
	reactor.run()