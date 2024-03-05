import re
import xml.etree.ElementTree as ET
from enum import Enum, auto


INT_PATTERN = r'[-+]?(?:[0-9]+|0o[0-7]+|0x[0-9A-Fa-f]+)\b'
BOOL_PATTERN = 'true|false'
TYPE_PATTERN = 'int|bool|string|nil'
VAR_PATTERN = '(GF|TF|LF)@'
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


class InvalidSymbolError(Exception):
    pass


class InvalidTypeError(Exception):
    pass


class InvalidEscapeSequenceError(Exception):
    pass


class Argument:
    def __init__(self, order: int, arg_type: ArgType, value: str):
        self.order = order
        self.arg_type = arg_type
        self.value = self._parse_value(value)

    def _parse_value(self, value: str):
        if self.arg_type == ArgType.VAR:
            if not re.match(VAR_PATTERN, value):
                raise InvalidSymbolError()
            return value

        if self.arg_type == ArgType.SYMB:
            if not re.match(SYMB_PATTERN, value):
                raise InvalidSymbolError()

            prefix, suffix = value.split('@', 1)

            if prefix in ['GF', 'TF', 'LF']:
                self.arg_type = ArgType.VAR
                return value
            elif not re.match(TYPE_PATTERN, prefix):
                raise InvalidTypeError()
            else:
                self.arg_type = ArgType[prefix.upper()]
                self._validate_literal(suffix)
                return suffix

        if self.arg_type == ArgType.TYPE:
            if not re.match(TYPE_PATTERN, value):
                raise InvalidTypeError()
            return value

        return value

    def _validate_literal(self, literal: str):
        if self.arg_type == ArgType.INT:
            if not re.match(INT_PATTERN, literal):
                raise InvalidSymbolError()

        elif self.arg_type == ArgType.BOOL:
            if not re.match(BOOL_PATTERN, literal):
                raise InvalidSymbolError()

        elif self.arg_type == ArgType.STRING:
            escapes = re.findall(ESCAPE_PATTERN, literal)

            if any(len(e) != 3 or not str(e).isdecimal() for e in escapes):
                raise InvalidEscapeSequenceError()


    def to_xml(self) -> ET.Element:
        element = ET.Element(f'arg{self.order}', { 'type': self.arg_type.name.lower() })
        element.text = self.value
        return element
