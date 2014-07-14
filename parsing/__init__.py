#!/usr/bin/python3
# -*- coding: utf-8 -*-

# == Global imports ==
import os, os.path, sys
from urllib.parse import urlparse
from urllib.request import urlretrieve
from urllib.error import URLError
from types import FunctionType, GeneratorType

# == Local imports ==
sys.path.append('../')

from exceptions import *
from validate import *
from pipes import Stream
from base import *
from sgml import *
from nodes import *

class Parser(Node):

    def __init__(self, xmlfile=''):
        super(Parser, self).__init__()
        # Tag types
        self.tags = {'!': self.newdecl,
                     '?': self.newpi,
                     '/': self.endelement}
        # SGML declaration types
        self.decls = {'ELEMENT': self.newcmodel,
                      'DOCTYPE': self.newdoctype,
                      'ATTLIST': self.newattlist,
                      'ENTITY': self.newentdef,
                      '--': self.newcomment}
        # Start parsing the source file
        if xmlfile:
            self(xmlfile)

    def newtag(self, stream, ancestors):
        char = next(stream)
        if char in self.tags:
            self.tags[char](stream, ancestors)
        else:
            test_name(self, char, stream, ancestors)
            test_doctype(self, char, stream, ancestors)
            self.newelement(stream, char, ancestors)

    def newattr(self, stream, ancestors):
        # Whoa! We just collected an attribute name!
        # Let's get its value, too.
        # Support for attribute name space will have to be added.
        for char in stream:
            # There may be spaces here, so we just
            # ignore them.
            if char == '"':
                break
        self.newval(stream, ancestors)

    def newval(self, stream, ancestors):
        self.newstr(stream, ancestors)
        data = ancestors.pop(-1)
        ancestors[-1].value(data)

    def newelement(self, stream, data, ancestors):
        # Tag parsing layer.
        # The tag may be opening an element, or
        # being autoclosed.
        # Namespace and name for the element.
        space = name = ''
        # The element's attributes
        # An attribute's namespace.
        keyspace = ''
        for char in stream:
            if char == ':':
                if not name:
                    space = data
                else:
                    keyspace = data
                data = ''
            elif char == ' ' and not name:
                # Unless the name is not yet defined, a space
                # is not something useful.
                name, data = Name(data, space), ''
                test_existence(self, name, stream, ancestors)
                test_parent(self, name, stream, ancestors)
                test_siblings(self, name, stream, ancestors)
                # Does it have valid siblings?
                # TODO: build tests.
                # Create the name object for the element,
                # composed of his namespace and name.
                new = Element(name, ancestors[-1])
                ancestors.append(new)
            elif char == '=':
                ancestors.append(Attribute(Name(data, keyspace)))
                self.newattr(stream, ancestors)
                attr = ancestors.pop(-1)
                ancestors[-1].append(attr)
                data = ''
            elif char == '/':
                for char in stream:
                    if char == '>':
                        break
                new = ancestors.pop(-1)
                ancestors[-1].append(new)
                break
            elif char == '>':
                if not name:
                    name = Name(data, space)
                    test_existence(self, name, stream, ancestors)
                    test_parent(self, name, stream, ancestors)
                    test_siblings(self, name, stream, ancestors)
                    data = ''
                    new = Element(name, ancestors[-1])
                    ancestors.append(new)
                break
            else:
                data += char

    def endelement(self, stream, ancestors):
        data = space = name = ''
        for char in stream:
            if char == ':':
                space, data = data, ''
            elif char == '>':
                name, data = data, ''
                new = ancestors.pop()
                test_closing(self, new, name, stream, ancestors)
                test_kids(self, new, stream, ancestors)
                ancestors[-1].append(new)
                break
            else:
                data += char

    def newpi(self, stream, ancestors):
        data = name = ''
        attrs = {}
        for char in stream:
            if char == ' ':
                # Unless the name is not yet defined, a space
                # is not something useful.
                if not name:
                    name, data = data, ''
                    # Create the name object for the element,
                    # composed of his namespace and name.
                    name = Name(name)
                    new = ProcessingInstruction(name, ancestors[-1])
                    ancestors.append(new)
            elif char == '=':
                ancestors.append(Attribute(Name(data)))
                self.newattr(stream, ancestors)
                attr = ancestors.pop(-1)
                ancestors[-1].append(attr)
                data = ''
            elif char == '?':
                # Oh, we reached the end of the P.I.
                for char in stream:
                    # There may be spaces here, so we just
                    # ignore them.
                    if char == '>':
                        break
                if not name:
                    name, data = data, ''
                    # Create the name object for the element,
                    # composed of his namespace and name.
                    name = Name(name)
                    new = ProcessingInstruction(name, ancestors[-1])
                    ancestors.append(new)
                else:
                    new = ancestors.pop(-1)
                ancestors[-1].append(new)
                break
            else:
                data += char

    def newdecl(self, stream, ancestors):
        data = ''
        new = False
        for char in stream:
            if char == ' ':
                if data in self.decls:
                    self.decls[data](stream, ancestors)
                    break
                else:
                    new = SGML(data)
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors)
            elif char == '[':
                # The right bracket means that there is an inline definition
                # embedded in the XML document. This means that it has to be parsed.
                # To do so, a new parent node is created (new = SGML(data)).
                if not new:
                    new = SGML(data)
                ancestors.append(new)
                # The inline definitions can then be read by the parser, and
                # appended to the document type.
                self.declcontent(stream, ancestors)
                # And at the end of the process, the dtd is taken off the ancestors
                # list to finish its parsing.
                new = ancestors.pop(-1)
            elif char == '>':
                ancestors[-1].append(new)
                break
            else:
                data += char

    def newcomment(self, stream, ancestors):
        data = ''
        for char in stream:
            if char == '-' and data.endswith('-'):
                ancestors[-1].append(MarkupComment(data[:-1]))
                next(stream)
                break
            else:
                data += char

    def newdoctype(self, stream, ancestors):
        data = ''
        for char in stream:
            if char == '"':
                # Well formed URLs and URNs are contained in \' and \"
                self.newstr(stream, ancestors)
                uri = ancestors.pop(-1)
                new.location.append(uri)
                # Obtain the doctype file if there is one.
                ancestors.append(new)
                self.dtdfile(uri, ancestors)
                new = ancestors.pop(-1)
            elif char == '[':
                # Inline definitions are present, see comment in newdecl.
                ancestors.append(new)
                self.declcontent(stream, ancestors)
                new = ancestors.pop(-1)
            elif char == ' ' and data:
                if data not in ('PUBLIC', 'SYSTEM'):
                    new = DocumentType(data)
                data = ''
            elif char == '>':
                ancestors[-1].append(new)
                break
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors)
            elif char != ' ':
                data += char

    def dtdfile(self, uri, ancestors):
        try:
            name = urlretrieve(str(uri))
        except (URLError, ValueError):
            name = [str(uri)]
        try:
            stream = Stream(file[0])
            self.declcontent(stream, ancestors)
        except FileNotFoundError as fnf:
            print('File', name[0], 'could not be found for DTD.')

    def newcmodel(self, stream, ancestors):
        data = ''
        for char in stream:
            if char == '>':
                ancestors[-1].append(ElementType(name, content))
                break
            elif char == ' ' and data:
                name = data
                data = ''
                try:
                    content = self.defkids(stream, ancestors, name)
                except EndOfTag:
                    break
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors)
            elif char != ' ':
                data += char

    def defkids(self, stream, ancestors=None, name=None):
        data, minoccur, maxoccur = '', 1, 1
        kids = ContentRef()
        for char in stream:
            if char == '(':
                if not kids:
                    kids = self.defkids(stream, ancestors)
                else:
                    data = self.defkids(stream, ancestors)
            elif char in seqtype:
                if not kids:
                    kids = seqtype[char]()
                if data in special_content:
                    kids.append(special_content[data](), minoccur, maxoccur)
                elif data:
                    kids.append(data, minoccur, maxoccur)
                data, minoccur, maxoccur = '', 1, 1
            elif char in occurs:
                if not data and kids:
                    kids.min, kids.max = minoccur, maxoccur
                else:
                    minoccur, maxoccur = occurs[char]
            elif char == ')':
                if data in special_content:
                    kids.append(special_content[data](), minoccur, maxoccur)
                elif data:
                    kids.append(data, minoccur, maxoccur)
                return kids
            elif char == '>':
                if data in special_content:
                    kids.append(special_content[data](), minoccur, maxoccur)
                elif data:
                    kids.append(data, minoccur, maxoccur)
                ancestors[-1].append(ElementType(name, kids))
                raise EndOfTag('The element def. decl. is over.')
            elif char == '%':
                self.newsysentref(stream, ancestors)
            elif char != ' ':
                data += char

    def newattlist(self, stream, ancestors, validate=False):
        data = ''
        for char in stream:
            if char == '>':
                name = data
                break
            if char in ('\n', ' ') and data:
                name = data
                data = ''
                attrs = self.defattrs(stream, ancestors)
                break
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors)
            elif char not in  ('\n', ' '):
                data += char
        mask = lambda x: isinstance(x, ElementType) and\
                         x.name == name
        element = list(ancestors[-1].filter(mask))
        if element:
            element_def = element[0]
            element_def.attrs.update(attrs)
        elif validate:
            raise ElementNotDefined('The element \'{}\' must be defined before it\
    is given attributes.'.format(name))

    def defattrs(self, stream, ancestors):
        data = ''
        name = ''
        attrs = {}
        for char in stream:
            if char == '>':
                if data and name:
                    attrs[name] = data
                return attrs
            elif char in ('\n', ' ') and name:
                attrs[name] = data
                name, data = '', ''
            elif char in ('\n', ' '):
                name = data
                data = ''
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors)
            elif char not in  ('\n', ' '):
                data += char

    def newentdef(self, stream, ancestors):
        data = ''
        name = ''
        value = ''
        system = False
        remote = False
        for char in stream:
            if char == '%':
                system = True
            elif char == ' ' and data == 'SYSTEM':
                remote = True
            elif char == ' ' and data:
                name, data = data, ''
            elif char == '"' and remote:
                self.newstr(stream, ancestors)
                address = ancestors.pop(-1)
                file = urlretrieve(uri)
                value = open(file[0], 'r').read()
            elif char == '"':
                self.newstr(stream, ancestors)
                value = ancestors.pop(-1)
            elif char == '>':
                new = EntityDefinition(name, value, system)
                ancestors[-1].append(new)
                break
            elif char != ' ':
                data += char

    def newsysentref(self, stream, ancestors, validate=False):
        name = ''
        for char in stream:
            if char == ';':
                break
            else:
                name += char
        mask = lambda x: isinstance(x, EntityDefinition) and (x.name == name)\
                         and x.system
        entdef = list(ancestors[-1].filter(mask, 0))
        if entdef:
            value = entdef[-1].value
            stream[:0] = list(value)
        elif validate:
            raise Exception('Entity Not Defined.')

    def newstr(self, stream, ancestors):
        data = ''
        fake_ancestors = [[Text('')]]
        for char in stream:
            if char == '"':
                ancestors.append(fake_ancestors[-1][-1] + Text(data))
                break
            elif char == '&':
                fake_ancestors[-1][-1].extend(Text(data))
                data = ''
                self.newentref(stream, fake_ancestors)
            else:
                data += char

    def declcontent(self, stream, ancestors, file=False, validate=False):
        for char in stream:
            if char == ']':
                break
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors)
            if char == '<':
                char = next(stream)
                if char == '!':
                    self.newdecl(stream, ancestors)
                elif char == '?':
                    self.newpi(stream, ancestors)
                elif valdiate:
                    raise Exception('This tag should be an SGML decl.')

    def newtext(self, ancestors, text):
        if len(ancestors[-1]) and isinstance(ancestors[-1][-1], Text):
            ancestors[-1][-1].extend(text)
        else:
            ancestors[-1].append(Text(text))

    def newentref(self, stream, ancestors, validate=False):
        name = ''
        for char in stream:
            if char == ';':
                break
            else:
                name += char
        if name in default_entities:
            self.newtext(ancestors, default_entities[name])
        elif name.startswith('#'):
            self.newtext(ancestors, chr(int(name[1:])))
        elif name.startswith('0x'):
            self.newtext(ancestors, chr(int(name[2:], 16)))
        elif name.startswith('0o'):
            self.newtext(ancestors, chr(int(name[2:], 8)))
        else:
            mask = lambda x: isinstance(x, EntityDefinition) and\
                             (x.name == name)\
                             and not x.system
            entdef = list(self.filter(mask, -1))
            if entdef:
                value = entdef[-1].value
                stream.insert(0, value)
            elif validate:
                raise Exception('Entity Not Defined.')
            else:
                with open('entities_to_define', 'a+') as ent2def:
                    print(name, file=ent2def)

    def __call__(self, source):
        if len(self):
            self.empty()
        # Temporary accumulated data (characters)
        data = ''
        # The last element in the list is the one to append new elements to
        ancestors = [self]
        # The source characters generator
        stream = Stream(source)
        for char in stream:
            # Basic parsing layer, to detect any context to get into
            if char == '<':
                self.newtext(ancestors, data)
                self.newtag(stream, ancestors)
                data = ''
            elif char == '&':
                # Entity reference layer
                self.newtext(ancestors, data)
                self.newentref(stream, ancestors)
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

if __name__ == '__main__':
    ## Active testing for the parser.
    file = '../source.xml'
    print('## == Now, a parser show off == ##')
    from timetools import Timer
    parser = Parser()
    timer = Timer()
    print('Let\'s go, New Parser!')
    for i in range(1):
        timer.start()
        parser(file)
        timer.stop()
    print(timer)
    print('The average is of', timer.totaltime/100)
    print('Printing the whole parser...')
    print(parser)
