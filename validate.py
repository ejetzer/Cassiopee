#!/usr/bin/python3.2
# -*- coding: utf-8 -*-

# == Global imports ==
import os, os.path
from urllib.parse import urlparse
from urllib.request import urlretrieve
from types import FunctionType, GeneratorType

# == Global constants ==
class Inf:
    '''This class represents all infinities. It's used for the '*' modifier.'''

    # Infinity is greater than everything else
    # (including itself for commodity)
    __gt__ = __ge__ = lambda x, y: True
    __lt__ = __le__ = lambda x, y: False

    # Inf is equal to all other infinities
    # (including those that are greater than itself...)
    __eq__ = lambda x, y: isinstance(y, Inf)
    __neq__ = lambda x, y: not isinstance(y, Inf)

    # I just wanted to be able to use it as a dict. entry.
    # See it as an Easter egg.
    # some_dict[Inf()] <=> some_dict['To infinity & beyond!']
    __hash__ = lambda x: hash('To infinity & beyond!')

# All the characters which cannot be used to start the name of:
#   (1) An element,
#   (2) Or an attribute.
badnamestart = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                '@', '#', '%', '^')
# Entities that need to be defiend for commodity and using ampersands.
default_entities = {'amp':'&', 'lt':'<', 'quot':'\"', 'apos':'\''}
# Modifiers in doctypes that specify how many of an element can exist
occurs = {'+': (1, Inf()), '?': (0, 1), '*': (0, Inf())}

# == Exceptions used in parsing ==
class EndOfTag(Exception):
    'The end of a tag has been reached. Raising an exception is the \
simplest way to move back up several levels in the parsing loop.'
    pass

# -- Validation Exceptions --

class InvalidMarkup(Exception):
    'Base class for all validation errors.'

    def __init__(self, explanation, context=[]):
        super().__init__(explanation)
        self.context = context

class ElementNotDefined(InvalidMarkup):
    pass

class InvalidNesting(InvalidMarkup):
    pass

class IllegalCharacter(InvalidMarkup):
    pass

class TagNotMatching(InvalidMarkup):
    pass

class NoDTDDefined(InvalidMarkup):
    pass

# == Validating functions ==

def test_name(self, char, stream, ancestors):
    if char in badnamestart and validate:
        raise IllegalCharacter('This character is not allowed at \
the beginning of an element name: \'' + char + '\'.',
                               (self,
                                char,
                                stream,
                                ancestors))

def test_doctype(self, char, stream, ancestors):
    mask = lambda x: isinstance(x, DocumentType)
    dtds = list(self.find(mask, -1))
    if not dtds:
        raise NoDTDDefined('There is no doctype to be found.',
                           (self,
                            char,
                            stream,
                            ancestors))
    elif len(dtds) > 1:
        raise NoDTDDefined('Not sure which doctype to use.',
                           (self,
                            char,
                            stream,
                            ancestors))

def test_existence(self, name, stream, ancestors):
    mask = lambda x: isinstance(x, DocumentType)
    doctype = next(self.filter(mask, -1))
    mask = lambda x: isinstance(x, ElementType) and x.name == name
    element_def = list(doctype.find(mask, 0))
    if not element_def:
        raise ElementNotDefined('This element is not defined.',
                                (self,
                                 name,
                                 stream,
                                 ancestors))

def test_parent(self, name, stream, ancestors):
    doctype = next(self.filter(lambda x: isinstance(x, DocumentType), 0))
    parents = list(doctype.find(lambda x: isinstance(x, ElementType) and\
                                          name in x.content and\
                                          ancestors[-1].name == x.name, 0))
    if len(ancestors) > 1 and not parents:
        raise InvalidNesting('Element \'{}\' has \
the wrong parent (\'{}\').'.format(name, ancestors[-1].name),
                             (self,
                              name,
                              stream,
                              ancestors))

def test_closing(self, new, name, stream, ancestors):
    if new.name != name:
        raise TagNotMatching('Tag {} has not been closed, and \
tag {} is begin closed. This is not allowed'.format(new.name, name),
                             (stream,
                              ancestors,
                              new,
                              name))

def test_siblings(self, name, stream, ancestors):
    parent = ancestors[-1]
    siblings = list(parent.filter(lambda x: isinstance(x, Element), 0))
    doctype = next(self.filter(lambda x: isinstance(x, DocumentType), 0))
    model = list(doctype.filter(lambda x: isinstance(x, ElementType) and\
                                          name in x.content and\
                                          x.name == ancestors[-1].name,
                                0))
    if parent is self and siblings:
        raise MultipleRoots('There is more than one root to this document!',
                            (stream,
                             ancestors,
                             new,
                             name))
    elif siblings:
        preceding = siblings[-1]
        ## Is it possible for "name" to follow "preceding"
        pass
    elif parent is not self:
        ## Is it possible for "name" to be the first element?
        pass
        

def test_kids(self, new, stream, ancestors):
    doctype = next(self.filter(lambda x: isinstance(x, DocumentType), 0))
    model = list(doctype.filter(lambda x: isinstance(x, ElementType) and\
                                          x.name == new.name,
                                0))[0].content
    content = list(new.filter(lambda x: isinstance(x, Element) or\
                                        x.collapse() not in ('', ' '),
                              0))
    print(repr(new), ':', content)
    last = content.pop()
    while isinstance(last, Text) and Text('') not in model:
        last = content.pop()
    good = False
    for ref in model.end():
        if last == ref:
            good = True
            break
    if not good:
        raise InvalidNesting('This is not where it belongs', [last,
                                                              model.end()])

# == Stream objects used by the parser ==
class Stream(list):

    def __iter__(self):
        return self

    def __next__(self):
        if self:
            return self.pop(0)
        else:
            raise StopIteration

    def __repr__(self):
        return '<Stream object at ' + str(hex(id(self))) + '>'

class File(list):
    '''Extended file class.'''

    def __init__(self, url):
        '''Load a local file.'''
        with open(url) as file:
            super(File, self).__init__(file.read())
        self.cursor = 0
        self.closed = False
        self.mode = 'a+'
        self.name = url

    def read(self, length=-1):
        '''Read characters.'''
        start = self.cursor
        end = self.cursor + length if length > -1 else -1
        self.cursor = end
        return self[start:end]

    def write(self, text, start=None):
        '''Insert characters.'''
        if start is not None:
            self.cursor = start
        self[self.cursor:self.cursor] = list(text)

    def __repr__(self):
        return '<XML File object: ' +\
               repr(''.join(self[0:6]))[:-1] + ' [...] ' +\
               repr(''.join(self[-5:]))[1:] + '>'

# == XML Tree Basic Classes ==
class Name:
    '''Name of an XML node.'''

    def __init__(self, name, space=''):
        self.name = name
        self.space = space

    def __repr__(self):
        return '<XML Element Name ' + self.space + ':' + self.name +\
               ' at ' + hex(id(self)) + '>'

    def __str__(self):
        return self.space + ':' + self.name

    def __str__(self):
        if self.space:
            return self.space + ':' + self.name
        else:
            return self.name

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self.name
        elif isinstance(other, Name):
            return other.name == self.name and other.space == self.space

    def __hash__(self):
        return hash(str(self))

class Node(list):
    '''XML Node.'''

    def __init__(self):
        # Variables used for normal behavior, as root of the DOM tree
        # Name of the element.
        self.name = Name('')
        # The root element has itself as a parent.
        self.parent = self

    def __getitem__(self, index):
        if isinstance(index, (tuple, list)):
            # If the index given is a tuple or a list,
            # each item specifies an index for a deeper level.
            current = self
            for level in index:
                current = current[level]
            return current
        elif isinstance(index, (str, dict, FunctionType)):
            # If the index is a string, function or dictionnary,
            # it is used as a filter.
            parent = Node()
            parent.extend(self.filter(index, -1))
            return parent
        else:
            return super().__getitem__(index)

    def __setitem__(self, index, value):
        if isinstance(index, (tuple, list)):
            current = self
            for level in index[:-1]:
                current = current[level]
            current[index[-1]] = value
        elif isinstance(index, (str, dict, FunctionType)):
            indexes = [i for i in self.find(index, -1)]
            for index in indexes:
                self[index] = value
        else:
            super().__setitem__(index, value)

    def __delitem__(self, index):
        if isinstance(index, (tuple, list)):
            current = self
            for level in index[:-1]:
                current = current[level]
            del current[index[-1]]
        elif isinstance(index, (str, dict, FunctionType)):
            indexes = [i for i in self.find(index, -1)]
            for index in indexes:
                del self[index]
        else:
            super().__delitem__(index)

    def __repr__(self):
        return '<XML Node ' + str(self.name) + ' at ' + hex(id(self)) + '>'

    def children(self, cond=lambda x: True, walk=0):
        '''Filter for child nodes.'''
        for child in self.filter(cond, walk):
            if isinstance(child, Element):
                yield child

    def siblings(self, cond=lambda x: True):
        '''Filter for sibling elements.'''
        for sibling in self.parent.children(cond):
            if isinstance(sibling, Element) and sibling is not self:
                yield sibling

    def preceding(self, cond=lambda x: True):
        '''Filter for preceding siblings.'''
        last = None
        for sibling in self.parent.children():
            if sibling is self:
                return last
            elif cond(sibling):
                last = sibling
        return None

    def following(self, cond=lambda x: True):
        '''Filter for following elements.'''
        over = False
        for sibling in self.parent.children():
            if sibling is self:
                over = True
            elif cond(sibling) and over:
                return sibling
        return None

    def brothers(self, cond=lambda x: True):
        '''Filter for immediatly adjacent elements.'''
        return [self.preceding(cond), self.following(cond)]

    def ancestors(self, cond=lambda x: True, walk=-1):
        '''Filter for ancestors.'''
        ancestor = self
        while True:
            new = ancestor.parent
            # If the new ancestor is equal to the one already in store,
            # it means the node is root.
            if new is not ancestor and walk != 0:
                walk -= 1
                ancestor = new
                if cond(ancestor):
                    yield ancestor
            else:
                break

    def find(self, cond=lambda x: True, walk=0):
        '''Return the index of matching nodes.'''
        # Using the function to determine which elements to find.
        for index, node in enumerate(self):
            if cond(node):
                yield (index,)
            if walk and isinstance(node, Node):
                for kid in node.find(cond, walk-1):
                    yield (index,) + kid

    def filter(self, cond=lambda x: True, walk=0):
        '''Return the matching nodes.'''
        for index in self.find(cond, walk):
            yield self[index]

    def replace(self, cond=lambda x: True, by=lambda x: x, walk=False):
        '''Replace a node using a filter.'''
        for index in self.find(cond, walk):
            self[index] = by(self[index])

    def empty(self):
        del self[:]

    @property
    def id(self, value=''):
        idattr = self.model.get('id', None)
        if value:
            self.attr(idattr, value)
        else:
            return self.attr(idattr)

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
        name = urlretrieve(uri)
        file = open(name[0], 'r')
        stream = Stream(file.read())
        self.declcontent(stream, ancestors)

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

    def newattlist(self, stream, ancestors):
        data = ''
        for char in stream:
            if char == '>':
                name = data
                break
            if char in ('\n', ' ') and data:
                name = data
                data = ''
                attrs = self.defattrs(stream)
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
        else:
            raise ElementNotDefined('The element \'{}\' must be defined before it\
    is given attributes.'.format(name))

    def defattrs(self, stream):
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

    def newsysentref(self, stream, ancestors):
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
        else:
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

    def declcontent(self, stream, ancestors, file=False):
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
                else:
                    raise Exception('This tag should be an SGML decl.')

    def newtext(self, ancestors, text):
        if len(ancestors[-1]) and isinstance(ancestors[-1][-1], Text):
            ancestors[-1][-1].extend(text)
        else:
            ancestors[-1].append(Text(text))

    def newentref(self, stream, ancestors):
        name = ''
        for char in stream:
            if char == ';':
                break
            else:
                name += char
        if name in default_entities:
            self.newtext(ancestors, default_entities[name])
        else:
            mask = lambda x: isinstance(x, EntityDefinition) and\
                             (x.name == name)\
                             and not x.system
            entdef = list(self.filter(mask, -1))
            if entdef:
                value = entdef[-1].value
                stream.insert(0, value)
            else:
                raise Exception('Entity Not Defined.')

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

class Text(list):

    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return '<Text node at ' + hex(id(self)) + '>'

    def __str__(self):
        return ''.join(self.collapse())

    def __hash__(self):
        return hash(str(self.collapse))

    def collapse(self):
        collapsed = Text('')
        for char in self:
            if char in ('\n', '\r', ' ', '\t'):
                if collapsed and collapsed[-1] == ' ':
                    continue
                else:
                    collapsed.append(' ')
            else:
                collapsed.append(char)
        return collapsed

    def startswith(self, text):
        for i, char in enumerate(text):
            if char != self[i]:
                return False
        return True

    def endswith(self, text):
        for i, char in enumerate(text[-1:-len(text):-1]):
            if char != self[-i-1]:
                return False
        return True

    def __add__(self, other):
        return Text([i for i in self] + [i for i in other])

    def __iadd__(self, other):
        self.extend(i for i in other)

    def __radd__(self, other):
        return Text([i for i in other] + [i for i in self])

    def escape(self):
        output = str(self)
        output = output.replace('&', '&amp;')
        output = output.replace('<', '&lt;')
        output = output.replace('\'', '&apos;')
        output = output.replace('\"', '&quot;')
        return output

# == XML Elements, Attributes & Processing Instructions ==
class ProcessingInstruction(Node):

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    def __repr__(self):
        return '<XML P.I. ' + str(self.name) + ' at ' + hex(id(self)) + '>'

    def __str__(self):
        if len(self):
            attributes = ' ' + ' '.join('{}="{}"'.format(   attr.name,
                                                            attr.value()) for\
                                                            attr in self)
        else:
            attributes = ''
        return '<?{}{}?>'.format(self.name, attributes)

class Element(Node):

    def __init__(self, name, parent=None):
        super().__init__()
        self.name = name
        self.parent = parent

    def __repr__(self):
        return '<XML Element ' + self.name.name + ' at ' + hex(id(self)) + '>'

    def __str__(self):
        attrs = [i for i in self.filter(lambda x: isinstance(x, Attribute))]
        if attrs:
            attributes = ' ' + ' '.join('{}="{}"'.format(attr.name,
                                               Text(attr.value()).escape()) for\
                                        attr in attrs)
        else:
            attributes = ''
        def mask(x):
            if isinstance(x, Attribute):
                return False
            elif isinstance(x, Text) and str(x) in (' ', '\n'):
                return False
            else:
                return True
        escape = lambda x: x.escape() if isinstance(x, Text) else x
        kids = [escape(i) for i in self.filter(mask)]
        if kids:
            return '<{}{}>\n    '.format(str(self.name), attributes) +\
                   '\n'.join(str(node.collapse()) if isinstance(node, Text)
                             else str(node) for node\
                             in kids).replace('\n', '\n    ') +\
                   '\n</{}>'.format(str(self.name))
        else:
            return '<{}{}/>'.format(str(self.name), attributes)

class Attribute(Node):

    def __init__(self, name, value=''):
        self.name = name
        self.__value = value

    def value(self, new=''):
        if new:
            self.__value = new
        else:
            return self.__value

# == SGML Tags: DOCTYPE, ELEMENT, ATTLIST & ENTDEF, along with Comments & ==
# == Entity References                                                    ==
class SGML(Node):

    def __init__(self, name, content=''):
        self.name = name
        self.value = content

    def __repr__(self):
        return '<SGML Declaration ' + self.name + ' at ' + hex(id(self)) + '>'

    def __str__(self):
        return '<!{} {}>'.format(self.name, self.value)

class DocumentType(SGML):

    def __init__(self, root, location=[], content=[]):
        self.name = 'DOCTYPE'
        self.root = root
        self.location = location
        self[:] = content[:]

    def __repr__(self):
        return '<Doctype Definition for ' + repr(self.root) +\
               ' at ' + hex(id(self)) + '>'

    def __str__(self):
        addr_type = 'PUBLIC' if len(self.location) == 2 else 'SYSTEM'
        location = '"{}"'.format(self.location[-1]) if addr_type == 'SYSTEM'\
                   else '"{}" "{}"'.format(*self.location)
        mask = lambda x: isinstance(x, SGML)
        content = '[\n{}\n]'.format('\n'.join(
                    str(i) for i in self.filter(mask)))
        content = content.replace('\n', '\n\t').replace('\t]', ']')
        return '<!DOCTYPE {} {} {} {}>'.format(self.root,
                                               addr_type,
                                               location,
                                               content)



# -- Element Type Descriptions --

class ContentRef(Node):

    def __init__(self, first=None, minoccur=1, maxoccur=1):
        super().__init__()
        self.min, self.max = minoccur, maxoccur
        if first:
            self.append(first, minoccur, maxoccur)

    ## Range comparison functions
    __lt__ = lambda self, other: self.max < other
    __gt__ = lambda self, other: self.min > other
    __ge__ = lambda self, other: self.max >= other
    __le__ = lambda self, other: self.min <= other
    __neq__ = lambda self, other: self[0] != other

    def __eq__(self, other):
        if isinstance(other, Element):
            return other.name == self[0]
        return self[0] == other
    __contains__ = __eq__

    def end(self):
        return set(self)
    
    def append(self, ref, minoccur=1, maxoccur=1):
        if not len(self):
            super().append(ref)
        else:
            self[0] = ref
        print(repr(self[0]))
        self.min, self.max = minoccur, maxoccur

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return '<Content Ref. for \'{}\' with between {} & {} occurences>'.\
               format(self[0], self.min, self.max)

    def __str__(self):
        return str(self[0])

class Choice(ContentRef):

    def end(self):
        return set(ref.end() for ref in self)

    def append(self, ref, minoccur=1, maxoccur=1):
        super(Node, self).append(ContentRef(ref, minoccur, maxoccur))

    def __contains__(self, other):
        for ref in self:
            if other in ref:
                return True
        return False

    def __str__(self):
        output = '('
        count = 0
        for ref in self:
            if count: output += ' | '
            else: count = 1
            mod = counters[(ref.min, ref.max)]
            if isinstance(ref, (Choice, Sequence)):
                output += '({}){}'.format(ref, mod)
            else:
                output += '{}{}'.format(ref, mod)
        output += ')' + counters[(self.min, self.max)]
        return output

class Sequence(ContentRef):

    def end(self):
        last = set()
        for bit in self[::-1]:
            if bit.min == 0:
                last.update(bit.end())
            elif bit >= 1:
                last.update(bit.end())
                return last
            else:
                last.update(bit.end())
        return last

    def append(self, ref, minoccur=1, maxoccur=1):
        super(Node, self).append(ContentRef(ref, minoccur, maxoccur))

    def __contains__(self, other):
        for ref in self:
            if other in ref:
                return True
        return False

    def __str__(self):
        output = '('
        count = 0
        for ref in self:
            if count: output += ', '
            else: count = 1
            mod = counters[(ref.min, ref.max)]
            if isinstance(ref, (Choice, Sequence)):
                output += '({}){}'.format(ref, mod)
            else:
                output += '{}{}'.format(ref, mod)
        output += ')' + counters[(self.min, self.max)]
        return output

class Any:

    __contains__ = __eq__ = lambda self, other: isinstance(other,
                                                           (Element, Text))

    def __str__(self):
        return 'ANY'

    def __hash__(self):
        return hash(str(self))

class Empty:

    __contains__ = __eq__ = lambda self, other: not other

    def __str__(self):
        return 'EMPTY'

    def __hash__(self):
        return hash(str(self))

class Characters:

    __contains__ = __eq__ = lambda self, other: isinstance(other, Text)

    def __str__(self):
        return '#PCDATA'

    def __hash__(self):
        return hash(str(self))

seqtype = {'|': Choice, ',': Sequence}
special_content = {'#PCDATA': Characters, 'ANY':Any, 'EMPTY':Empty}
counters = {(0, 1):'?', (1, 1): '', (0, Inf()):'*', (1, Inf()):'+'}

class ElementType(SGML):

    def __init__(self, name, content=Sequence(), attrs={}):
        self.name = name
        self.content = content
        # Make a shallow copy, because otherwise all element types will refer
        # to the same attribute list.
        self.attrs = attrs.copy()

    def __repr__(self):
        return '<Element Definition for ' + repr(self.name) +\
               ' at ' + hex(id(self)) + '>'

    def __eq__(self, other):
        if self.name != other.name:
            return False
        elif self.content != other:
            return False
        for attr in other.attrs:
            if attr not in self.attrs:
                return False
        return True

    def __str__(self):
        output = '<!ELEMENT {} {}>'.format(self.name, self.content)
        if self.attrs:
            output += '\n<!ATTLIST {} {}>'.format(self.name,
                                    '\n\t'.join(str(attr) + ' ' +\
                                    str(self.attrs[attr])\
                                    for attr in self.attrs))
        return output

class EntityDefinition(SGML):

    def __init__(self, name, value, system=False):
        self.name = name
        self.value = value
        self.system = system

    def __eq__(self, other):
        return other.name == self.name

    def __str__(self):
        system = ' % ' if self.system else ' '
        return '<!ENTITY{}{} "{}">'.format(system, self.name,
                                           self.value.escape())

class MarkupComment(SGML):

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return '<Comment at ' + hex(id(self)) + '>'

    def __str__(self):
        return '<!-- {} -->'.format(self.content)

if __name__ == '__main__':
    ## Active testing for the parser.
    file = File('source.xml')
    print('## == Now, a parser show off == ##')
    from timetools import Timer
    parser = Parser()
    timer = Timer()
    print('Let\'s go, New Parser!')
    for i in range(100):
        timer.start()
        try:
            parser(file)
        except Exception as mistake:
            print(mistake)
            for i in mistake.context:
                print(repr(i))
            break
        finally:
            timer.stop()
    print(timer)
    print('The average is of', timer.totaltime/100)
    print('Printing the whole parser...')
    print(parser)
