# == Validating functions ==

def test_name(self, char, stream, ancestors, validate=False):
    if not validate: return False
    if char in badnamestart:
        raise IllegalCharacter('This character is not allowed at \
the beginning of an element name: \'' + char + '\'.',
                               (self,
                                char,
                                stream,
                                ancestors))

def test_doctype(self, char, stream, ancestors, validate=False):
    if not validate: return False
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

def test_existence(self, name, stream, ancestors, validate=False):
    if not validate: return False
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

def test_parent(self, name, stream, ancestors, validate=False):
    if not validate: return False
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

def test_closing(self, new, name, stream, ancestors, validate=False):
    if not validate: return False
    if new.name != name:
        raise TagNotMatching('Tag {} has not been closed, and \
tag {} is begin closed. This is not allowed'.format(new.name, name),
                             (stream,
                              ancestors,
                              new,
                              name))

def test_siblings(self, name, stream, ancestors, validate=False):
    if not validate: return False
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
        

def test_kids(self, new, stream, ancestors, validate=False):
    if not validate: return False
    # Figure out what the doctype is:
    doctype = next(self.filter(lambda x: isinstance(x, DocumentType), 0))
    # From the doctype, take the model for this element:
    model = list(doctype.filter(lambda x: isinstance(x, ElementType) and\
                                    x.name == new.name,
                                0))[0].content
    # Obtain all the non-null kids of the current element:
    content = list(new.filter(lambda x: isinstance(x, Element) or\
                                        str(x) not in ('', ' '),
                              0))
    last = content.pop()
    # Eliminate superflous spaces. Basically; strip().
    while isinstance(last, Text) and Text('') not in model:
        last = content.pop()
    good = False
    for ref in model.end():
        if getattr(last, 'name', Text('')) == ref:
            good = True
            break
    if not good:
        raise InvalidNesting('This is not where it belongs', [last,
                                                              model.end()])
