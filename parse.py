import sys
import xml.etree.ElementTree as ET

from instruction import *


class ParserError(Exception):
    pass


class Parser:
    def __init__(self):
        self.instructions: list[Instruction] = []
        self.header_parsed = False
        self.line_count = 0

    def _parse_header(self, line: str):
        """Parse the mandatory header and set a flag if successful."""
        if line.lower() != '.ippcode24':
            sys.exit(21)
        self.header_parsed = True

    def _parse_instruction(self, line: str):
        """Parse a line and convert it to an instruction."""
        words = line.split()

        try:
            # Construct an instruction object and add it to the list of instructions
            instruction = Instruction(len(self.instructions) + 1, words[0], words[1:])
            self.instructions.append(instruction)
        except InvalidOpcodeError:
            sys.exit(22)
        except Exception as e:
            print(f'Line {self.line_count}: {e}', file=sys.stderr)
            sys.exit(23)

    def _strip_comment(self, line: str) -> str:
        """Remove the part after # from a string and return it."""
        hash_pos = line.find('#')
        if hash_pos != -1:
            line = line[:hash_pos]
        return line

    def parse(self) -> ET.ElementTree:
        """Read IPPcode24 from standard input and return its XML representation."""
        for line in sys.stdin:
            self.line_count += 1
            line = self._strip_comment(line).strip() # Strip comments and surrounding whitespace

            # Blank line or just a comment -- skip it.
            if line == '':
                continue

            # Try to parse the header line if it has not been found yet,
            # otherwise treat it as an instruction.
            if not self.header_parsed:
                self._parse_header(line)
            else:
                self._parse_instruction(line)

        if not self.header_parsed:
            # The header has not been found and there are no more lines
            sys.exit(21)

        root = ET.Element('program', { 'language': 'IPPcode24' }) # Create a root element

        # Convert all parsed instructions to XML and append them
        for instruction in self.instructions:
            root.append(instruction.to_xml())

        # Prettify and return the XML tree
        tree = ET.ElementTree(root)
        ET.indent(tree)
        return tree


if __name__ == '__main__':
    parser = Parser()
    program = parser.parse()

    program.write(sys.stdout.buffer, encoding='UTF-8', xml_declaration=True)
