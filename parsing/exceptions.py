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
