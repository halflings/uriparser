#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    uriparser
    A (somewhat) comprehensive URI parsing library with both strict and "tolerant" parsing, urlencoding,
    and normalization.
"""

import json
import re

def urlencode_char(char):
    """ Percent-encodes a character """
    if len(char) > 1:
        raise ValueError("Expected a single character, got a string of characters.")
    return '%{}'.format(char.encode('hex')).upper()

def urlencode_str(string):
    """ Percent-encodes a string """
    return ''.join(c if re.match(Uri.UNRESERVED_CHAR, c) else urlencode_char(c) for c in string)


class Uri(object):
    """ Utility class to handle URIs """

    SCHEME_REGEX = "[a-z][a-z0-9+.-]"
    UNRESERVED_CHAR = "[a-zA-Z0-9\-._~]"
    HOST_PATTERN =  "[a-z\.\-]+"

    @staticmethod
    def unreserved(string):
        """ Checks that the given string is only made of "unreserved" characters """
        return len(re.findall("(?!{})".format(Uri.UNRESERVED_CHAR), string)) == 1

    @staticmethod
    def valid_hostname(hostname):
        """ Checks if the given hostname is valid """
        return len(re.findall("(?![a-z0-9\.\-])", hostname)) == 1
    
    def __init__(self, uri, strict=False):
        """ Parses the given URI """
        uri = uri.strip()

        # URI scheme is case-insensitive
        self.scheme = uri.split(':')[0].lower()

        if not re.match(Uri.SCHEME_REGEX, self.scheme):
            raise ValueError("Invalid URI scheme: '{}'".format(self.scheme))

        self.path = uri[len(self.scheme) + 1:]

        # URI fragments
        self.fragment = None
        if '#' in self.path:
            self.path, self.fragment = self.path.split('#')

        # Query parameters (for instance: http://mysite.com/page?key=value&other_key=value2)
        self.parameters = dict()
        if '?' in self.path:
            separator = '&' if '&' in self.path else ';'
            query = '?'.join(self.path.split('?')[1:])
            query_params = query.split(separator)
            query_params = map(lambda p : p.split('='), query_params)

            if not Uri.unreserved(query.replace('=', '').replace(separator, '')):     
                if strict:
                    raise ValueError('Invalid query: {}'.format(query))
                else:
                    query_params = [map(urlencode_str, couple) for couple in query_params]

            self.parameters = {key : value for key, value in query_params}
            self.path = self.path.split('?')[0]


        # For URIs that have a path starting with '//', we try to fetch additional info:
        self.authority = None
        if self.path.startswith('//'):
            self.path = self.path.lstrip('//')
            uri_tokens = self.path.split('/')

            self.authority = uri_tokens[0]
            self.hostname = self.authority
            self.path = self.path[len(self.authority):]

            # Fetching authentication data. For instance: "http://login:password@site.com"
            self.authenticated = '@' in self.authority
            if self.authenticated:
                self.user_information, self.hostname = self.authority.split('@')
                
                # Validating userinfo
                if not Uri.unreserved(self.user_information.replace(':', '')):
                    if strict:
                        raise ValueError("Invalid user information: '{}'".format(self.user_information))
                    else:
                        userinfo_tokens = self.user_information.split(':')
                        self.user_information = ':'.join(map(urlencode_str, userinfo_tokens))

            # Fetching port
            self.port = None
            if ':' in self.hostname:
                self.hostname, self.port = self.hostname.split(':')
                try:
                    self.port = int(self.port)
                    if not 0 <= self.port <= 65535:
                        raise ValueError
                except ValueError:
                    raise ValueError("Invalid port: '{}'".format(self.port))

            # Hostnames are case-insensitive
            self.hostname = self.hostname.lower()

            # Validating the hostname and path
            if not Uri.valid_hostname(self.hostname):
                raise ValueError("Invalid hostname: '{}'".format(self.hostname))
            
            if self.path and not Uri.unreserved(self.path.replace('/', '')):
                if strict:
                    raise ValueError("Invalid path: '{}'".format(self.path))
                else:
                    path_tokens = self.path.split('/')
                    self.path = '/'.join(map(urlencode_str, path_tokens))

        elif len(self.path.split('@')) > 2 or not Uri.unreserved(self.path.split('@')[-1]):
            raise ValueError("Invalid path: '{}'".format(self.path))

    def remove_fragment(self):
        """ Removes any fragment from the URI """
        self.fragment = None

    def remove_query(self):
        """ Removes any query from the URI """
        self.parameters = dict()

    def query(self):
        """ Returns a serialized representation of the query parameters. """
        return '&'.join('{}={}'.format(key, value) for key, value in sorted(self.parameters.iteritems()))

    def summary(self):
        """ Summary of the URI object. Useful for debugging. """
        uri_repr = '{}\n'.format(self)
        uri_repr += '\n'
        uri_repr += "* Scheme name: '{}'\n".format(self.scheme)

        if self.authority:
            uri_repr += "* Authority path: '{}'\n".format(self.authority)

            uri_repr += "  . Hostname: '{}'\n".format(self.hostname)
            if self.authenticated:
                uri_repr += "  . User information = '{}'\n".format(self.user_information)
            if self.port:
                uri_repr += "  . Port = '{}'\n".format(self.port)

        uri_repr += "* Path: '{}'\n".format(self.path)
        if self.parameters:
            uri_repr += "* Query parameters: '{}'\n".format(self.parameters)
        if self.fragment:
            uri_repr += "* Fragment: '{}'\n".format(self.fragment)
        return uri_repr

    def json(self):
        """ JSON serialization of the URI object """
        return json.dumps(self.__dict__, sort_keys=True, indent=2)

    def __str__(self):
        """ Outputs the URI as a normalized string """
        uri = '{}:'.format(self.scheme)
        
        if self.authority:
            uri += '//'
            if self.authenticated:
                uri += self.user_information + '@'
            uri += self.hostname
            if self.port:
                uri += ':{}'.format(self.port)

        uri += self.path
        if self.parameters:
            uri += '?' + self.query()
        if self.fragment:
            uri += '#' + urlencode_str(self.fragment)
        return uri

    def __eq__(self, uri):
        """ Equivalence between two URIs: the equivalence of their respective normalized string representation """
        return str(self) == str(uri)


if __name__ == '__main__':

    print '~ '*40
    print '~ URIPARSER unit-tests'
    print '~ '*40
    print ''

    total_tests = total_passed = 0

    print '* Testing a very complex URI (with all possible fields)'
    uri = Uri('foo://username:password@example.com:8042/over/there/index.dtb?type=animal&name=narwhal#nose')

    tests, passed = 7, 0
    passed += uri.scheme == 'foo'
    passed += uri.user_information == 'username:password'
    passed += uri.authority and uri.hostname == 'example.com'
    passed += uri.authority and uri.port == 8042
    passed += 'type' in uri.parameters and uri.parameters['type'] == 'animal'
    passed += uri.fragment == 'nose'
    passed += uri.path == '/over/there/index.dtb'
    print '   . {}/{} passed'.format(passed,tests)

    total_tests += tests
    total_passed += passed

    print '* Testing URIs without an "authority part"'
    uri = Uri('mailto:username@example.com?subject=Topic')
    tests, passed = 3, 0
    passed += uri.scheme == 'mailto'
    passed += uri.path == 'username@example.com'
    passed += 'subject' in uri.parameters and uri.parameters['subject'] == 'Topic'

    print '   . {}/{} passed'.format(passed,tests)

    total_tests += tests
    total_passed += passed

    print '* Testing "url normalization"'
    uri = Uri('HTTP://eXamPLE.CoM')
    uri_bis = Uri('http://example.com')
    tests, passed = 1, 0
    passed += uri == uri_bis

    print '   . {}/{} passed'.format(passed,tests)
    total_tests += tests
    total_passed += passed

    print '* Testing the "tolerant" parsing mode and percent-encoding'
    tests, passed = 2, 0

    try:
        uri = Uri('mailto:quora.com?Subject=lol wat iz url éncoding ?', strict=False)
        passed += 1
    except ValueError:
        pass
    passed += 'Subject' in uri.parameters and uri.parameters['Subject'] == 'lol%20wat%20iz%20url%20%C3%A9ncoding%20%3F'
    
    print '   . {}/{} passed'.format(passed,tests)
    total_tests += tests
    total_passed += passed

    print '* Testing a broken URI in the strict mode'
    tests, passed = 1, 0
    try:
        uri = Uri('http://invalid_hostnéme . com')
    except ValueError:
        passed += 1
    print '   . {}/{} passed'.format(passed,tests)
    total_tests += tests
    total_passed += passed

    print '- '*40
    print 'TOTAL: Passed {}/{} tests'.format(total_passed, total_tests)