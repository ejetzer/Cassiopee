import sys
sys.path.append('../..')

from Cassiopee.parsing.base import *

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
        return frozenset(self)
    
    def append(self, ref, minoccur=1, maxoccur=1):
        if not len(self):
            super().append(ref)
        else:
            self[0] = ref
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
        kids = set()
        for ref in self:
            kids.update(ref.end())
        return frozenset(kids)

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
        for bit in self[-1::-1]:
            if bit.min == 0:
                last.update(bit.end())
            elif bit >= 1:
                last.update(bit.end())
                return last
            else:
                last.update(bit.end())
        return frozenset(last)

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
