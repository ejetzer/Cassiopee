#!/usr/bin/python3
# -*- coding: utf-8 -*-

# == Global imports ==
import os, os.path, sys
from urllib.parse import urlparse
from urllib.request import urlretrieve
from urllib.error import URLError
from pathlib import Path
from types import FunctionType, GeneratorType

# == Local imports ==
sys.path.append('../')

from parsing.exceptions import *
from parsing.validate import *
from parsing.pipes import Stream
from parsing.base import *
from parsing.sgml import *
from parsing.nodes import *

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

    def newtag(self, stream, ancestors, validate=False):
        char = next(stream)
        if char in self.tags:
            self.tags[char](stream, ancestors, validate)
        else:
            if validate:
                test_name(self, char, stream, ancestors)
                test_doctype(self, char, stream, ancestors)
            self.newelement(stream, char, ancestors, validate)

    def newattr(self, stream, ancestors, validate=False):
        # Whoa! We just collected an attribute name!
        # Let's get its value, too.
        # Support for attribute name space will have to be added.
        for char in stream:
            # There may be spaces here, so we just
            # ignore them.
            if char == '"':
                break
        self.newval(stream, ancestors, validate)

    def newval(self, stream, ancestors, validate=False):
        self.newstr(stream, ancestors, validate)
        data = ancestors.pop(-1)
        ancestors[-1].value(data)

    def newelement(self, stream, data, ancestors, validate=False):
        # Tag parsing layer.
        # The tag may be opening an element, or
        # being autoclosed.
        # Namespace and name for the element.
        space, name = '', ''
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
                if validate:
                    test_existence(self, name, stream, ancestors)
                    test_parent(self, name, stream, ancestors)
                    test_siblings(self, name, stream, ancestors)
                # Create the name object for the element,
                # composed of his namespace and name.
                new = Element(name, ancestors[-1])
                ancestors.append(new)
            elif char == '=':
                ancestors.append(Attribute(Name(data, keyspace)))
                self.newattr(stream, ancestors, validate)
                attr = ancestors.pop(-1)
                ancestors[-1].append(attr)
                data = ''
            elif char == '/':
                self.endelement(stream, ancestors, validate)
                break
            elif char == '>':
                if not name:
                    name = Name(data, space)
                    if validate:
                        test_existence(self, name, stream, ancestors)
                        test_parent(self, name, stream, ancestors)
                        test_siblings(self, name, stream, ancestors)
                    data = ''
                    new = Element(name, ancestors[-1])
                    ancestors.append(new)
                break
            else:
                data += char

    def endelement(self, stream, ancestors, validate=False):
        data, space, name = '', '', ''
        for char in stream:
            if char == ':':
                space, data = data, ''
            elif char == '>':
                name, data = data, ''
                new = ancestors.pop()
                if validate:
                    test_closing(self, new, name, stream, ancestors)
                    test_kids(self, new, stream, ancestors)
                ancestors[-1].append(new)
                break
            else:
                data += char

    def newpi(self, stream, ancestors, validate=False):
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
                self.newattr(stream, ancestors, validate)
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

    def newdecl(self, stream, ancestors, validate=False):
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
                self.newsysentref(stream, ancestors, validate)
            elif char == '[':
                # The right bracket means that there is an inline definition
                # embedded in the XML document. This means that it has to be parsed.
                # To do so, a new parent node is created (new = SGML(data)).
                if not new:
                    new = SGML(data)
                ancestors.append(new)
                # The inline definitions can then be read by the parser, and
                # appended to the document type.
                self.declcontent(stream, ancestors, validate)
                # And at the end of the process, the dtd is taken off the ancestors
                # list to finish its parsing.
                new = ancestors.pop(-1)
            elif char == '>':
                ancestors[-1].append(new)
                break
            else:
                data += char

    def newcomment(self, stream, ancestors, validate=False):
        data = ''
        for char in stream:
            if char == '-' and data.endswith('-'):
                ancestors[-1].append(MarkupComment(data[:-1]))
                next(stream)
                break
            else:
                data += char

    def newdoctype(self, stream, ancestors, validate=False):
        data = ''
        for char in stream:
            if char == '"':
                # Well formed URLs and URNs are contained in \' and \"
                self.newstr(stream, ancestors, validate)
                uri = ancestors.pop(-1)
                new.location.append(uri)
                # Obtain the doctype file if there is one.
                ancestors.append(new)
                self.dtdfile(uri, ancestors, validate)
                new = ancestors.pop(-1)
            elif char == '[':
                # Inline definitions are present, see comment in newdecl.
                ancestors.append(new)
                self.declcontent(stream, ancestors, validate)
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
                self.newsysentref(stream, ancestors, validate)
            elif char != ' ':
                data += char

    def dtdfile(self, uri, ancestors, validate=False):
        name = urlparse(str(uri))
        loc = Path(name.path)
        tmp = Path('tmp')
        if not tmp.exists(): tmp.mkdir()
        if name.scheme and name.netloc:
            with urlopen(name) as file:
                with (tmp / loc).open('w') as cache:
                    cache.write(file.read())
        else:
            with loc.open('r') as file:
                with (tmp / loc).open('w') as cache:
                    cache.write(file.read())
        stream = Stream(tmp / loc)
        self.declcontent(stream, ancestors, validate)

    def newcmodel(self, stream, ancestors, validate=False):
        data = ''
        for char in stream:
            if char == '>':
                ancestors[-1].append(ElementType(name, content))
                break
            elif char == ' ' and data:
                name = data
                data = ''
                try:
                    content = self.defkids(stream, ancestors, name, validate)
                except EndOfTag:
                    break
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors, validate)
            elif char != ' ':
                data += char

    def defkids(self, stream, ancestors=None, name=None, validate=False):
        data, minoccur, maxoccur = '', 1, 1
        kids = ContentRef()
        for char in stream:
            if char == '(':
                if not kids:
                    kids = self.defkids(stream, ancestors, validate=validate)
                else:
                    data = self.defkids(stream, ancestors, validate=validate)
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
                self.newsysentref(stream, ancestors, validate)
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
                attrs = self.defattrs(stream, ancestors, validate)
                break
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors, validate)
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

    def defattrs(self, stream, ancestors, validate=False):
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
                self.newsysentref(stream, ancestors, validate)
            elif char not in  ('\n', ' '):
                data += char

    def newentdef(self, stream, ancestors, validate=False):
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
                self.newstr(stream, ancestors, validate)
                address = ancestors.pop(-1)
                file = urlretrieve(uri)
                value = open(file[0], 'r').read()
            elif char == '"':
                self.newstr(stream, ancestors, validate)
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
            pos = stream.tell()
            start = pos - len(name) - 2
            stream[start:pos] = str(value.escape())
            stream.seek(start)
        elif validate:
            raise Exception('Entity Not Defined.')

    def newstr(self, stream, ancestors, validate=False):
        data = ''
        fake_ancestors = [[Text('')]]
        for char in stream:
            if char == '"':
                ancestors.append(fake_ancestors[-1][-1] + Text(data))
                break
            elif char == '&':
                fake_ancestors[-1][-1].extend(Text(data))
                data = ''
                self.newentref(stream, fake_ancestors, validate)
            else:
                data += char

    def declcontent(self, stream, ancestors, file=False, validate=False):
        for char in stream:
            if char == ']':
                break
            elif char == '%':
                # Call for a new entity reference
                self.newsysentref(stream, ancestors, validate)
            if char == '<':
                char = next(stream)
                if char == '!':
                    self.newdecl(stream, ancestors, validate)
                elif char == '?':
                    self.newpi(stream, ancestors, validate)
                elif valdiate:
                    raise Exception('This tag should be an SGML decl.')

    def newtext(self, ancestors, text, validate=False):
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
            self.newtext(ancestors, default_entities[name], validate)
        elif name.startswith('#'):
            self.newtext(ancestors, chr(int(name[1:])), validate)
        elif name.startswith('0x'):
            self.newtext(ancestors, chr(int(name[2:], 16)), validate)
        elif name.startswith('0o'):
            self.newtext(ancestors, chr(int(name[2:], 8)), validate)
        else:
            mask = lambda x: isinstance(x, EntityDefinition) and\
                             (x.name == name)\
                             and not x.system
            entdef = list(self.filter(mask, -1))
            if entdef:
                value = entdef[-1].value
                pos = stream.tell()
                start = pos - len(name) - 2
                stream[start:pos] = str(value.escape())
                stream.seek(start)
            elif validate:
                raise Exception('Entity Not Defined.')
            else:
                with open('entities_to_define', 'a+') as ent2def:
                    print(name, file=ent2def)

    def __call__(self, loc, validate=False):
        if len(self):
            self.empty()
        # Temporary accumulated data (characters)
        data = ''
        # The last element in the list is the one to append new elements to
        ancestors = [self]
        # The source characters generator
        loc = Path(loc)
        cwd = os.getcwd()
        os.chdir(str(loc.parent))
        stream = Stream(loc.name)
        for char in stream:
            # Basic parsing layer, to detect any context to get into
            if char == '<':
                self.newtext(ancestors, data, validate)
                self.newtag(stream, ancestors, validate)
                data = ''
            elif char == '&':
                # Entity reference layer
                self.newtext(ancestors, data, validate)
                self.newentref(stream, ancestors, validate)
                data = ''
            else:
                data += char
        os.chdir(cwd)

    def __repr__(self):
        return '<XML Parser at ' + hex(id(self)) + '>'

    def __str__(self):
        mask = lambda x: str(x) not in ('\n', ' ') if isinstance(x, Text)\
                                                   else True
        escape = lambda x: x.escape() if isinstance(x, Text) else x
        return '\n'.join(str(escape(node)) for node in self.filter(mask))

