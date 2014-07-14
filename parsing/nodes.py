from base import *

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
