import json

class Uri(object):
    
    ESCAPE_CODES = {' ' : '%20', '<' : '%3C', '>' : '%3E', '#' : '%23', '%' : '%25', '{' : '%7B',
                    '}' : '%7D', '|' : '%7C', '\\' : '%5C', '^' : '%5E', '~' : '%7E', '[' : '%5B',
                    ']' : '%5D', '`' : '%60', ';' : '%3B', '/' : '%2F', '?' : '%3F', ':' : '%3A',
                    '@' : '%40', '=' : '%3D', '&' : '%26', '$' : '%24'}
    @staticmethod
    def escape(string):
        """ URI-escapes the given string """
        return ''.join(c if not c in Uri.ESCAPE_CODES else Uri.ESCAPE_CODES[c] for c in string)

    def __init__(self, uri):
        uri = uri.strip().lower()

        self.scheme = uri.split(':')[0]
        self.path = uri[len(self.scheme) + 1:]

        # URI fragments
        self.fragment = None
        if '#' in self.path:
            self.path, self.fragment = self.path.split('#')

        # Query parameters (for instance: http://mysite.com/page?key=value&other_key=value2)
        self.parameters = dict()
        if '?' in self.path:
            separator = '&' if '&' in self.path else ';'
            query_params = self.path.split('?')[-1].split(separator)
            query_params = map(lambda p : p.split('='), query_params)
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

            # Fetching port
            self.port = None
            if ':' in self.hostname:
                self.hostname, self.port = self.hostname.split(':')

            self.authority = '//' + self.authority


    # URI Parameters
    def set_parameter(self, key, value):
        self.parameters[key] = Uri.escape(value)

    def remove_parameter(self, key):
        if key in self.parameters:
            del self.parameters[key]

    def serialize_parameters(self):
        """ Returns a string representation of the uri parameters. """
        return '&'.join('{}={}'.format(key, value) for key, value in sorted(self.parameters.iteritems()))


    # String representation
    def __str__(self):
        uri = '{}:'.format(self.scheme)
        
        if self.authority:
            if self.authenticated:
                uri += self.user_information
                uri += '@'
            uri += self.hostname
            if self.port:
                uri += ':{}'.format(self.port)

        uri += self.path
        if self.parameters:
            uri += '?' + self.serialize_parameters()
        if self.fragment:
            uri += '#' + self.fragment
        return uri

    # JSON serialization of the URI object
    def json(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=2)

    # Summary of the URI object. Mostly for debug.
    def summary(self):
        uri_repr = '{}\n'.format(self)
        uri_repr += '\n'
        uri_repr += "* Schema name: '{}'\n".format(self.scheme)
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

if __name__ == '__main__':
    examples = {'foo://username:password@example.com:8042/over/there/index.dtb?type=animal&name=narwhal#nose',
                'mailto:username@example.com?subject=Topic',
                'http://truc.com/lien?key=value#ha'}

    for uri_str in examples:
        uri = Uri(uri_str)
        print uri_str, ':'
        print '-'*len(uri_str)
        print uri.summary()
        print uri.json()
        print ''

