"""OAuth Proxy"""

from setuptools import setup, find_packages

setup(
    name="oauth-proxy",
    version="1.0.0",
    url="http://github.com/mojodna/oauth-proxy",
    license="BSD License",
    description="OAuth HTTP proxy",
    keywords="oauth proxy twisted",
    packages=find_packages(),
    scripts=["bin/oauth-proxy"],
    install_requires=["twisted>=8.2.0", "oauth>=1.0.1"],
    author="Seth Fitzsimmons",
    author_email="seth@mojodna.net",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "Topic :: Internet :: Proxy Servers",
        "License :: OSI Approved :: BSD License",
    ],
)
