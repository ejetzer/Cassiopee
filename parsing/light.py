class LightParser(Node):

    def __init__(self, xmlfile=None):
        super().__init__()
        self.tags = {'!': self.newdecl,
                     '?': self.newpi,
                     '/': self.endelement}
        if xmlfile: self(xmlfile)

    def newtag(self, stream, ancestors=[], validate=False):
        char = next(stream)
        if char in self.tags:
            self.tags[char](stream, ancestors, validate)
        else:
            self.newelement(stream, char, ancestors, validate)

    def newelement_handler(self, name, ancestors=[], validate=False):
        pass

    def newelement(self, stream, data, ancestors=[], validate=False):
        space, name = '', ''
        keyspace = ''
        for char in stream:
            if char == ':':
                if not name: space = data
                else: keyspace = data
                data = ''
            elif char == ' ' and not name:
                name, data = Name(data, space), ''
                self.newelement_handler(name, ancestors, validate)
            elif char == '=':
                name, data = Name(data, keyspace), ''
                self.newattr(stream, name, ancestors, validate)
            elif char == '/':
                self.endelement(stream, ancestors, validate)
                break
            elif char == '>' and not name:
                name, data = Name(data, space), ''
                self.newelement_handler(name, ancestors, validate)
                break
            else:
                data += char

    def endelement_handler(self, name, ancestors=[], validate=False):
        pass

    def endelement(self, stream, ancestors=[], validate=False):
        data, space, name = '', '', ''
        for char in stream:
            if char == ':': space, data = data, ''
            elif char == '>':
                name, data = Name(name, space), ''
                self.endelement_handler(name, ancestors, validate)
                break
            else:
                data += char

    def newpi_handler(self, name, ancestors=[], validate=False):
        pass

    def endpi_handler(self, name, ancestors=[], validate=False):
        pass

    def newpi(self, stream, ancestors=[], validate=False):
        data, name = '', ''
        for char in stream:
            if char == ' ' and not name:
                name, data = Name(data), ''
                self.newpi_handler(name, ancestors, validate)
            elif char == '=':
                name, data = Name(data), ''
                self.newattr(stream, name, ancestors, validate)
            elif char == '?':
                for char in stream: if char == '>': break
                if not name:
                    name, data = Name(name), ''
                    self.newpi_handler(name, ancestors, validate)
                self.endpi_handler(name, ancestors, validate)
            else:
                data += char

    def newstr(self, stream, ancestors=[], validate=False):
        pass

    def newtext(self, stream, text, ancestors=[], validate=False):
        pass

    def newentref(self, stream, ancestors=[], validate=False):
        pass

    def newattr(self, stream, name, ancestors=[], validate=False):
        self.newattr_handler(name, ancestors, validate)
        pass

    def newdecl(self, stream, ancestors=[], validate=False):
        pass

    def __call__(self, loc, validate=False):
        if len(self): self.empty()
        data, ancestors = '', [self]
        stream = FileCopy(loc)
        for char in stream:
            if char == '<':
                self.newtext(stream, data, ancestors, validate)
                self.newtag(stream, ancestors, validate)
            elif char == '&':
                self.newtext(stream, data, ancestors, validate)
                self.newentref(stream, ancestors, validate)
                data = ''
            else:
                data += char

    def __repr__(self):
        return '<XML Parser at ' + hex(id(self)) + '>'

    def __str__(self):
        mask = lambda x: str(x) not in ('\n', ' ') if isinstance(x, Text)\
                                                   else True
        escape = lambda x: x.escape() if isinstance(x, Text) else x
        return '\n'.join(str(escape(node)) for node in self.filter(mask))


class SGMLParser(LightParser):

    def __init__(self, xmlfile=None):
        self.decls = {'ELEMENT': self.newcmodel,
                      'DOCTYPE': self.newdoctype,
                      'ATTLIST': self.newattlist,
                      'ENTITY': self.newentdef,
                      '--': self.newcomment}
        super().__init__(xmlfile)

    def newdecl(self, stream, ancestors=[], validate=False):
        pass

    def newcomment(self, stream, ancestors=[], validate=False):
        pass

    def newdoctype(self, stream, ancestors=[], validate=False):
        pass

    def dtdfile(self, stream, ancestors=[], validate=False):
        pass

    def newcmodel(self, stream, ancestors=[], validate=False):
        pass

    def defkids(self, stream, ancestors=[], validate=False):
        pass

    def newattlist(self, stream, ancestors=[], validate=False):
        pass

    def defattrs(self, stream, ancestors=[], validate=False):
        pass

    def newentdef(self, stream, ancestors=[], validate=False):
        pass

    def newsysentref(self, stream, ancestors=[], valdiate=False):
        pass

    def declcontent(self, stream, ancestors=[], file=False, validate=False):
        pass
