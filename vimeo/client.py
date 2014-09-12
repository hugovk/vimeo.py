#! /usr/bin/env python
# encoding: utf-8

from functools import wraps
import requests
from auth.client_credentials import ClientCredentialsMixin
from auth.authorization_code import AuthorizationCodeMixin
from upload import UploadMixin

class VimeoClient(ClientCredentialsMixin, AuthorizationCodeMixin, UploadMixin):
    """Client handle for the Vimeo API."""

    API_ROOT = "https://api.vimeo.com"
    HTTP_METHODS = {'head', 'get', 'post', 'put', 'patch', 'options', 'delete'}
    ACCEPT_HEADER = "application/vnd.vimeo.*;version=3.2"

    def __init__(self, token=None, key=None, secret=None, *args, **kwargs):
        """Prep the handle with the authentication information."""
        self.token = token
        self.app_info = (key, secret)
        self._requests_methods = dict()

        # Make sure we have enough info to be useful.
        assert token is not None or (key is not None and secret is not None)

    # Internally we back this with an auth mechanism for Requests.
    @property
    def token(self):
        return self._token.token
    @token.setter
    def token(self, value):
        self._token = _BearerToken(value) if value else None

    def __getattr__(self, name):
        """This is where we get the function for the verb that was just
        requested.

        From here we can apply the authentication information we have.
        """
        if name not in self.HTTP_METHODS:
            raise AttributeError("%r is not an HTTP method" % name)

        # Get the Requests based function to use to preserve their defaults.
        request_func = getattr(requests, name, None)
        if request_func is None:
            raise AttributeError("%r could not be found in the backing lib"
                % name)

        @wraps(request_func)
        def caller(url, *args, **kwargs):
            """Hand off the call to Requests."""
            headers = kwargs.get('headers', dict())
            headers['Accept'] = self.ACCEPT_HEADER
            kwargs['headers'] = headers

            if not url[:4] == "http":
                url = self.API_ROOT + url

            return request_func(
                url,
                auth=self._token,
                *args, **kwargs)

        return caller

class _BearerToken(requests.auth.AuthBase):
    """Model the bearer token and apply it to the request."""
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer ' + self.token
        return request
