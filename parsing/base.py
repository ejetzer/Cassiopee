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
default_entities = {'amp':'&', 'lt':'<', 'quot':'\"', 'apos':'\'',
                    'gt':'>', 'copy':'©'}
# Modifiers in doctypes that specify how many of an element can exist
occurs = {'+': (1, Inf()), '?': (0, 1), '*': (0, Inf())}

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
