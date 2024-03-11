import xml.etree.ElementTree as ET

from argument import *
from parse import ParserError


OPCODE_PATTERN = '[A-z]+'


INSTRUCTION_SET = {
    'MOVE': [ArgType.VAR, ArgType.SYMB],
    'CREATEFRAME': [],
    'PUSHFRAME': [],
    'POPFRAME': [],
    'DEFVAR': [ArgType.VAR],
    'CALL': [ArgType.LABEL],
    'RETURN': [],
    'PUSHS': [ArgType.SYMB],
    'POPS': [ArgType.VAR],
    'ADD': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'SUB': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'MUL': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'IDIV': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'LT': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'GT': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'EQ': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'AND': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'OR': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'NOT': [ArgType.VAR, ArgType.SYMB],
    'INT2CHAR': [ArgType.VAR, ArgType.SYMB],
    'STRI2INT': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'READ': [ArgType.VAR, ArgType.TYPE],
    'WRITE': [ArgType.SYMB],
    'CONCAT': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'STRLEN': [ArgType.VAR, ArgType.SYMB],
    'GETCHAR': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'SETCHAR': [ArgType.VAR, ArgType.SYMB, ArgType.SYMB],
    'TYPE': [ArgType.VAR, ArgType.SYMB],
    'LABEL': [ArgType.LABEL],
    'JUMP': [ArgType.LABEL],
    'JUMPIFEQ': [ArgType.LABEL, ArgType.SYMB, ArgType.SYMB],
    'JUMPIFNEQ': [ArgType.LABEL, ArgType.SYMB, ArgType.SYMB],
    'EXIT': [ArgType.SYMB],
    'DPRINT': [ArgType.SYMB],
    'BREAK': [],
}


class InvalidOpcodeError(Exception):
    pass


class Instruction:
    def __init__(self, order: int, opcode: str, args: list[str]):
        self.order = order
        self.opcode = self._parse_opcode(opcode)
        self.expected_args = INSTRUCTION_SET[self.opcode]
        self.args = self._parse_args(args)

    def _parse_opcode(self, opcode) -> str:
        if re.match(OPCODE_PATTERN, opcode) == None:
            raise ParserError('Syntax error, expected opcode')

        opcode = opcode.upper()

        if not opcode in INSTRUCTION_SET:
            raise InvalidOpcodeError()

        return opcode

    def _parse_args(self, args) -> list[Argument]:
        res = []

        if len(args) != len(self.expected_args):
            raise ParserError(f'Bad argument count, expected {len(self.expected_args)} argument(s)')

        for i, arg in enumerate(args):
            argument = Argument(i + 1, self.expected_args[i], arg)
            res.append(argument)

        return res

    def to_xml(self) -> ET.Element:
        attrib = { 'order': str(self.order), 'opcode': self.opcode }
        element = ET.Element('instruction', attrib)

        for arg in self.args:
            element.append(arg.to_xml())

        return element
