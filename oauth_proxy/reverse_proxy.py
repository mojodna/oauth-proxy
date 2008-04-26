from twisted.internet import reactor
from twisted.python import usage
from twisted.web import proxy
import urlparse

class Options(usage.Options):
	synopsis = "Usage: oauth_reverse proxy --remote-host <remote host> [--remote-port <remote port>] [--path-prefix <path prefix>] [-p <proxy port>] [--ssl] [--ssl-private-key <private key] [--ssl-certificate <certificate>]"
	longdesc = "Makes an OAuth reverse HTTP proxy server.."
	optParameters = [
		['path-prefix',		None, '',	"Path prefix"],
		['port', 'p',		8080, "Proxy port", int],
		['remote-host',		None, None, "Remote host"],
		['remote-port',		None, 80,	"Remote port"],
		['ssl-certificate', None, None, "SSL certificate"],
		['ssl-private-key', None, None, "SSL private key"],
	]

	optFlags = [['ssl', 's']]



class OAuthValidator:
	def validate(self):
		"""Validate an OAuth request"""
		return True



class OAuthReverseProxyRequest(proxy.ReverseProxyRequest):
	# TODO this class may be unnecessary if header rewriting can occur in OAuthReverseProxyResource
		
	proxyClientFactoryClass = ProxyClientFactory

	def __init__(self, validator, *args):
		self.validator = validator
		proxy.ReverseProxyRequest.__init__(self, *args)


	def process(self):
		# This logic either goes here or in OAuthReverseProxyResource.render
		
		# filter querystring from self.uri
		
		# filter headers from self.getAllHeaders()
		
		# validate oauth params
		valid = True
		
		if valid:
			proxy.ReverseProxyRequest.process(self)
			# looks like: 
			# self.received_headers['host'] = self.factory.host
			# clientFactory = self.proxyClientFactoryClass(
			#	  self.method, self.uri, self.clientproto, self.getAllHeaders(),
			#	  self.content.read(), self)
			# self.reactor.connectTCP(self.factory.host, self.factory.port,
			#						  clientFactory)
		else:
			# return an error message
			pass



class OAuthReverseProxy(proxy.ReverseProxy):

	# TODO this may be the only required line, if validation occurs in OAuthReverseProxyResource
	# requestFactory = OAuthReverseProxyRequest

	def __init__(self, validator):
		self.validator = validator
		proxy.ReverseProxy.__init__(self)


	def requestFactory(self, *args):
		return OAuthReverseProxyRequest(self.validator, *args)



class OAuthReverseProxyResource(proxy.ReverseProxyResource):
	def __init__(self, host, port, path, reactor=reactor, validator=OAuthValidator):
		self.validator = validator
		proxy.ReverseProxyResource(self, host, port, path, reactor)


	def getChild(self, path, request):
		return OAuthReverseProxyResource(
			self.host, self.port, self.path + '/' + urlquote(path, safe="", validator=self.validator))


	def render(self, request):
		# get OAuth headers from request.received_headers['authorization']
		
		# remove OAuth headers
		
		# parse querystring and POST body for OAuth params
		qs = urlparse.urlparse(request.uri)[4]
		
		# rewrite the path w/o OAuth params
		
		# validate signature
		
		valid = self.validator.validate()
		
		if valid:
			response = proxy.ReverseProxyResource.render(self, request)
		else:
			# render an error message
			# TODO return NOT_DONE_YET in order to write headers
			response = "Invalid signature"
		
		return response
