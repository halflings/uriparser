uriparser
=========
### Work in progress!
URI parser for Python that supports many schemes (URLs, mailto, ...)

### Example:
Doing this...
    uri_str = 'foo://username:password@example.com:8042/over/there/index.dtb?type=animal&name=narwhal#nose'
    uri = Uri(uri_str)
    print uri.summary()

...will output:

    foo://username:password@example.com:8042/over/there/index.dtb?name=narwhal&type=animal#nose
    * Schema name: 'foo'
    * Authority path: '//username:password@example.com:8042'
      . Hostname: 'example.com'
      . User information = '//username:password'
      . Port = '8042'
    * Path: '/over/there/index.dtb'
    * Query parameters: '{'type': 'animal', 'name': 'narwhal'}'
    * Fragment: 'nose'
