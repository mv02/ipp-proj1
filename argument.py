import re
import xml.etree.ElementTree as ET
from enum import Enum, auto

from parse import ParserError


INT_PATTERN = r'[-+]?(?:[0-9]+|0o[0-7]+|0x[0-9A-Fa-f]+)\b'
LABEL_PATTERN = r'[A-z_\-$&%*!?][0-9A-z_\-$&%*!?]*'
TYPE_PATTERN = 'int|bool|string|nil'
VAR_PATTERN = r'(GF|TF|LF)@[A-z_\-$&%*!?][0-9A-z_\-$&%*!?]*'
SYMB_PATTERN = '(GF|TF|LF|int|bool|string|nil)@'
ESCAPE_PATTERN = r'(?<=\\).{0,3}'


class ArgType(Enum):
    INT = auto()
    BOOL = auto()
    STRING = auto()
    NIL = auto()
    LABEL = auto()
    TYPE = auto()
    VAR = auto()
    SYMB = auto()


class Argument:
    def __init__(self, order: int, arg_type: ArgType, value: str):
        self.order = order
        self.arg_type = arg_type
        self.value = self._parse_value(value)

    def _parse_value(self, value: str) -> str:
        """Parse and return the argument's value."""
        if self.arg_type == ArgType.LABEL:
            return self._parse_label(value)
        if self.arg_type == ArgType.TYPE:
            return self._parse_type(value)
        if self.arg_type == ArgType.VAR:
            return self._parse_variable(value)
        if self.arg_type == ArgType.SYMB:
            return self._parse_symbol(value)
        return value

    def _parse_label(self, value: str) -> str:
        """Parse a label argument value."""
        if not re.fullmatch(LABEL_PATTERN, value):
            raise ParserError('Invalid label name')
        return value

    def _parse_type(self, value: str) -> str:
        """Parse a type argument value."""
        if not re.fullmatch(TYPE_PATTERN, value):
            raise ParserError('Invalid type')
        return value

    def _parse_variable(self, value: str) -> str:
        """Parse a variable argument value."""
        if not re.fullmatch(VAR_PATTERN, value):
            raise ParserError('Invalid variable identifier')
        return value

    def _parse_symbol(self, value: str) -> str:
        """Parse a symbol argument value. This can be a variable or a constant."""
        # The symbol must contain @, otherwise we cannot distinguish its two parts later.
        if not '@' in value:
            raise ParserError('Invalid symbol, expected variable or constant')

        if re.fullmatch(VAR_PATTERN, value):
            # The symbol is a variable
            self.arg_type = ArgType.VAR
            return value

        prefix, suffix = value.split('@', 1)

        if re.fullmatch(TYPE_PATTERN, prefix):
            # The symbol is a constant -- set the argument type accordingly.
            self.arg_type = ArgType[prefix.upper()]
            # Validate the literal after @ and return it as argument value
            self._validate_literal(suffix)
            return suffix

        # The symbol does not have a valid frame nor data type prefix
        raise ParserError('Invalid symbol, expected variable or constant')

    def _validate_literal(self, literal: str):
        """Validate given literal based on the argument type."""
        # Integer in decimal, hexadecimal or octal format
        if self.arg_type == ArgType.INT and not re.fullmatch(INT_PATTERN, literal):
            raise ParserError('Invalid literal')

        # bool@true or bool@false
        elif self.arg_type == ArgType.BOOL and literal not in ['true', 'false']:
            raise ParserError('Invalid literal')

        # String containing only 3 digit long escape sequences
        elif self.arg_type == ArgType.STRING:
            escapes = re.findall(ESCAPE_PATTERN, literal)
            if any(len(e) != 3 or not str(e).isdecimal() for e in escapes):
                raise ParserError('Invalid escape sequence')

        # nil@nil, nothing else is allowed
        elif self.arg_type == ArgType.NIL and literal != 'nil':
            raise ParserError('Invalid literal')

    def to_xml(self) -> ET.Element:
        """Return an XML representation of the argument."""
        element = ET.Element(f'arg{self.order}', { 'type': self.arg_type.name.lower() })
        element.text = self.value
        return element
