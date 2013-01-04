#!/usr/bin/python3.2
# -*- coding: utf-8 -*-

from selectors import *

class Block(list):

    def __init__(self, name, content=[]):
        self.name = name
        self[:] = content[:]

class Atrule(Block):
    pass

class Media(Atrule):

    def __init__(self, medias=['all'], styles=[]):
        self.name = 'media'
        self.medias = medias
        self[:] = styles[:]

    def __hash__(self):
        return hash(tuple(self.medias))

    def __eq__(self, other):
        if isinstance(other, str) and other in self.medias:
            return True
        elif isinstance(other, (list, tuple)) and list(other) == self.medias:
            return True
        else:
            return False

    def __repr__(self):
        return '(' + ', '.join(media for media in self.medias) + ')'

class Import(Media):

    def __init__(self, medias='all', location=None):
        self.name = 'import'
        self.medias = medias
        # This will have to be implemented using the URL objects from www.py
        self.location = location

class Styles(Block):

    def __init__(self, selector, properties={}):
        self.name = selector
        self.properties = properties

class StylesComment:

    def __init__(self, comment=''):
        self.comment = comment

class Stylesheet(Block):

    def __init__(self, source=''):
        super().__init__('')
        if source:
            self(source)

    def __call__(self, source):
        self.feed(source)

    def media(self, media=Media(), stylesheet=None):
        if media and stylesheet:
            self.medias[media] = stylesheet
        else:
            styles = Media(media.medias)
            for medias in self.medias:
                if medias == media:
                    total.extend(media)
            return styles

    def encoding(self, coding=''):
        if coding:
            self.coding = coding
            # The encoding is enforced when the stylesheet is 'printed'.
        else:
            return self.coding

    def styles(self, selector, styles=None):
        pass

    def newatrule(self, stream, ancestors):
        data = ''
        for char in stream:
            if char in ' {':
                if data == 'import':
                    self.newimport(stream, ancestors)
                elif data == 'media':
                    self.newmedia(stream, ancestors)
                elif data == 'charset':
                    self.newcoding(stream, ancestors)
            else:
                data += char

    def newimport(self, stream, ancestors):
        pass

    def newmedia(self, stream, ancestors):
        medias = ['']
        for char in stream:
            if char == ',':
                medias.append('')
            elif char == '{':
                ancestors.append(Media(medias))
            elif char != ' ':
                medias[-1] += char

    def newcoding(self, stream, ancestors):
        data = ''
        for char in stream:
            if char == '"':
                data = self.newstring(stream)
                break
        self.encoding(data)
        for char in stream:
            if char == ';':
                break

    def newstring(self, stream):
        data = ''
        for char in stream:
            if char == '\\':
                data += next(stream)
                # I will have to add some way to support Unicode here.
            elif char == '"':
                return data
            else:
                data += char

    def newselector(self, stream, ancestors):
        print()
        print('I am in newselectors. What is happening?')
        try:
            print('Attempting to parse Selectors through \
the already made parser.')
            selector = Selectors()
            selector.feed(stream)
            ## NOTE: There has to be a way to detect comment in selectors.
            ##          It must be integrated with the selector parser,
            ##          And allow the parser to resume exactly where it left.
            ##          Suggestions:
            ##              - Raise an exception & save the parser state;
            ##              - Transform the whole selector parser into a huge
            ##                generator and yield when there is a comment.
            print('The process, has failed somehow.')
        except EndOfSelectors:
            print('The end of the selector has been reached.')
            # Find properties and values
            properties = {}
            print('Let us start finding properties.')
            for char in stream:
                if char == '}':
                    print('The block is over.')
                    print('# Starting self.newselector.')
                    self.newselector(stream, ancestors)
                    break
                elif char not in (' ', '\r', '\n'):
                    print('We have encountered the first non-space character!')
                    print('Warping to the property & value parser...')
                    name, value = self.newprop(stream, ancestors, char)
                    print('The name of the property is', name,
                          'and its value is', value, '.')
                    # Eventually, this will assign values to a restricted set
                    # of properties, due to the need of rendering. e.g. :
                    # font: italic bold normal 10pt/1 "Arial", sans-serif;
                    #                           |
                    #                           V
                    # {font-style: italic,
                    #  font-weight: bold,
                    #  etc. }
                    print('Assigning the property.')
                    properties[name] = value
                    print('The property is now registered! Cheers!')
            print('We must create a block to store all the properties \
and the selector')
            block = Styles(selector, properties)
            print('The block has been created...')
            ancestors[-1].append(block)
            print('...and appended to the current media.')

    def newprop(self, stream, ancestors, data=''):
        print()
        print('\tWarped into the propery parser.')
        print('\tSearching for the property name.')
        name = data
        for char in stream:
            if char == ':':
                print('\tEnd of the property\'s name.')
                print('\tThe name happens to be', name)
                print('\tStart looking for its value.')
                value = self.newval(stream, ancestors)
                print('\tThe value is now', value, '.')
                break
            elif char != ' ':
                print('\tNon space character, let us store it.')
                name += char
        print('\tReturn the name and value.')
        print()
        return name, value

    def newval(self, stream, ancestors):
        value = ''
        for char in stream:
            if char == ';':
                # This loop ends only when it encounters a valid
                # end-of-instruction marker (';'). It happens regularly that
                # the marker is forgotten when writing code. The desired
                # behavior is to treat the instruction correctly anyway.
                # It will be implemented in the future.
                return value
            elif char in ('"', "'"):
                value += self.newstring(stream)
            else:
                value += char

    def newcomment(self, stream, ancestors):
        data = ''
        for char in stream:
            if char == '*':
                nextchar = next(stream)
                if nextchar == '/':
                    ancestors[-1].append(StylesComment(data))
                    break
                else:
                    data += char + nextchar
            else:
                data += char

    def feed(self, source):
        print('# Feed the source to the beast.')
        stream = (i for i in source)
        print('# The stream is', repr(stream), '.')
        ancestors = [Media()]
        print('# Ancestors are', repr(ancestors), '.')
        print('# Starting self.newselector.')
        self.newselector(stream, ancestors)
        print('# The beast has been fed.')
        self.extend(ancestors)

# Adapt the selector parser to accept CSS comments in parts of the selectors.
# The only place where a selector is not accepted, or will be analyzed wrongly,
# is in the middle of a name token. Betwen tokens, or at the beginning or end
# of the selector, there is no problem with comments.

def init(self, selector=''):
        '''Create a selector based upon the given argument:
    If given a str or gen, parses it;
    If given a list, takes its value;
    If given a dict, appends it.
'''
        ## All the different flags used in CSS selectors, mapped to their
        ## parsing functions.
                         # ID flag. Matches a special attribute, determined
                         # in the document type.
        self.switches = {'#': self.setid,
                         # Selects a class. Only in HTML. Or maybe using
                         # the same mechanism as for IDs.
                         '.': self.setclass,
                         # Beginning of an attribute selector.
                         '[': self.setattribute,
                         # Beginning of a pseudo-element or of a
                         # pseudo-class.
                         ':': self.setpseudo,
                         # Denotes a first level child.
                         '>': self.setchild,
                         # Denotes a following sibling.
                         '~': self.setsibling,
                         # Denotes an adjacent and following sibling.
                         '+': self.setbrother,
                         # Denotes any descendant.
                         ' ': self.setdescendant,
                         # Separates two selectors.
                         ',': self.newselector,
                         # Beginning of a block, end of the selectors.
                         # (added for use inside a CSS stylesheet.
                         '{': self.endselectors,
                         # The beginning of a comment, or a
                         # forbidden character.
                         '/': self.comment}
        if isinstance(selector, (str, GeneratorType)):
            # If the argument is a string or a generator, then it is parsed.
            self.feed(selector)
        elif isinstance(selector, list):
            # If the argument is a list, it replaces the parsed values.
            self[:] = selector[:]
        elif isinstance(selector, dict):
            # If the argument is a dictionnary, then it is appended as a
            # simple selector.
            self.append(selector)

def comment(self, stream):
        if next(stream) == '*':
            data = ''
            for char in stream:
                if char == '*':
                    nextchar = next(stream)
                    if nextchar == '/':
                        if 'comments' in self[-1]:
                            self[-1]['comments'].append(StylesComment(data))
                        else:
                            self[-1]['comments'] = [StylesComment(data)]
                        break
                    else:
                        data += char + nextchar
                else:
                    data += char
        else:
            raise InvalidCharacter

Selectors.__init__ = init
Selectors.comment = comment

if __name__ == '__main__':
    with open('source.css') as source:
        output = Stylesheet(source.read())
        for media in output:
            for selector in media:
                print(selector.name)
                for prop in selector.properties:
                    print('\t{}: {}'.format(prop, selector.properties[prop]))
