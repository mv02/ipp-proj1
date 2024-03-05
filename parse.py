import sys
import xml.etree.ElementTree as ET

from instruction import *


class Parser:
    def __init__(self):
        self.instructions: list[Instruction] = []
        self.header_parsed = False

    def _parse_header(self, line: str):
        if line.lower() != '.ippcode24':
            sys.exit(21)
        self.header_parsed = True

    def _parse_instruction(self, line: str):
        words = line.split()

        try:
            instruction = Instruction(len(self.instructions) + 1, words[0], words[1:])
            self.instructions.append(instruction)
        except InvalidOpcodeError:
            sys.exit(22)
        except:
            sys.exit(23)

    def _strip_comment(self, line: str) -> str:
        hash_pos = line.find('#')
        if hash_pos != -1:
            line = line[:hash_pos]
        return line

    def parse(self):
        for line in sys.stdin:
            line = self._strip_comment(line).strip()

            if line == '':
                continue

            if not self.header_parsed:
                self._parse_header(line)
            else:
                self._parse_instruction(line)

        if not self.header_parsed:
            sys.exit(21)

        root = ET.Element('program', { 'language': 'IPPcode24' })

        for instruction in self.instructions:
            root.append(instruction.to_xml())

        tree = ET.ElementTree(root)
        ET.indent(tree)
        return tree


if __name__ == '__main__':
    parser = Parser()
    program = parser.parse()

    program.write(sys.stdout.buffer, encoding='UTF-8', xml_declaration=True)
