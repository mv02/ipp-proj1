import sys
import xml.etree.ElementTree as ET

from instruction import *


JUMP_INSTRUCTIONS = ['CALL', 'RETURN', 'JUMP', 'JUMPIFEQ', 'JUMPIFNEQ']

HELP_STRING = """Usage: parse.py [--help | --stats FILE [ENTRIES] [--stats FILE [ENTRIES]] ... ]
Read IPPcode24 source code from standard input, validate it and print XML representation of the program to standard output.

Option --stats can be used to print ENTRIES to FILE(s).

ENTRIES can be any combination of the following:

  --loc            print number of lines with instructions
  --comments       print number of lines with comments
  --labels         print number of defined labels
  --jumps          print number of jump instructions
  --fwjumps        print number of forward jumps
  --backjumps      print number of backward jumps
  --badjumps       print number of jumps to a non-existent label
  --frequent       print opcodes ordered by number of uses
  --print=STRING   print STRING
  --eol            print a blank line"""


class ParserError(Exception):
    pass


class OptionsError(Exception):
    pass


class Parser:
    def __init__(self):
        self.instructions: list[Instruction] = []
        self.header_parsed = False
        self.line_count = 0
        self.labels: dict[str, int] = {}
        self.opcodes: dict[str, int] = {}
        self.frequent: list[str] = []
        self.count: dict[str, int] = {
            'comments': 0,
            'jumps': 0,
            'fwjumps': 0,
            'backjumps': 0,
            'badjumps': 0,
        }

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
            self.count['comments'] += 1
            line = line[:hash_pos]
        return line

    def _calculate_stats(self):
        """Calculate input program statistics and save them."""
        for instruction in self.instructions:
            # Increment number of this opcode occurences
            if instruction.opcode in self.opcodes:
                self.opcodes[instruction.opcode] += 1
            else:
                self.opcodes[instruction.opcode] = 1

            # Save defined label and its location in the program
            if instruction.opcode == 'LABEL':
                self.labels[instruction.args[0].value] = instruction.order

        # Choose the most frequent opcodes
        self.frequent = sorted([x[0] for x in self.opcodes.items() if x[1] == max(self.opcodes.values())])

        jump_instructions = filter(lambda x: x.opcode in JUMP_INSTRUCTIONS, self.instructions)

        # Calculate number of jumps
        for instruction in jump_instructions:
            self.count['jumps'] += 1

            # RETURN instruction does not jump to a label -- skip it.
            if instruction.opcode == 'RETURN':
                continue

            label = instruction.args[0].value

            if label not in self.labels:
                # Jump to a non-existent label
                self.count['badjumps'] += 1
            elif self.labels[label] > instruction.order:
                # Forward jump
                self.count['fwjumps'] += 1
            else:
                # Backward jump
                self.count['backjumps'] += 1

    def _get_stats_entry(self, name: str) -> str:
        """Return the string representation of a stats item."""
        if name == 'loc':
            return str(len(self.instructions))
        if name == 'labels':
            return str(len(self.labels))
        if name == 'frequent':
            return ','.join(self.frequent)
        if name in self.count:
            return str(self.count[name])
        if name.startswith('print='):
            return name.split('=', 1)[1]
        if name == 'eol':
            return ''
        raise OptionsError('Invalid stats item')

    def _print_stats_group(self, filename: str, group: list[str]):
        """Print given group of stats entries into a file."""
        try:
            with open(filename, 'w') as f:
                for entry in group:
                    print(self._get_stats_entry(entry), file=f)
        except OSError:
            sys.exit(11)

    def print_stats(self, options: list[str]):
        """Print stats groups to files based on given options."""
        self._calculate_stats()

        stats_groups: dict[str, list[str]] = {}
        stats_pos = [i for i, x in enumerate(options) if x == '--stats'] # Positions of 'stats' in the options list

        for i, pos in enumerate(stats_pos):
            if pos + 1 >= len(options):
                # There are no more arguments after --stats
                raise OptionsError('Invalid argument combination, expected filename after --stats')

            filename = options[pos + 1] # The following option is the filename

            # Preparing to slice this stats group's entries
            start = pos + 2
            end = len(options)

            if i + 1 < len(stats_pos):
                # There is another stats group after this one -- slicing only up to --stats.
                end = stats_pos[i + 1]

            if filename in stats_groups:
                # Writing multiple stats groups into the same file
                sys.exit(12)

            stats_groups[filename] = [x.removeprefix('--') for x in options[start:end]]

        # Print parsed stats groups to files
        for filename, group in stats_groups.items():
            self._print_stats_group(filename, group)

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


def parse_input_args() -> list[str]:
    """Parse command line arguments and return a list of them."""
    if any(arg == '--help' for arg in sys.argv[1:]):
        # No other arguments are allowed with --help
        if len(sys.argv) > 2:
            raise OptionsError('Invalid argument combination')

        print(HELP_STRING)
        sys.exit()

    # No arguments are allowed before --stats
    if len(sys.argv) > 1 and sys.argv[1] != '--stats':
        raise OptionsError('Unexpected argument')

    return sys.argv[1:]


if __name__ == '__main__':
    # Parse command line arguments
    try:
        args = parse_input_args()
    except OptionsError as e:
        print(e, file=sys.stderr)
        sys.exit(10)

    # Perform IPPcode24 parsing
    parser = Parser()
    program = parser.parse()

    # Print parsing stats if requested
    if len(args) > 0:
        try:
            parser.print_stats(args)
        except OptionsError as e:
            print(e, file=sys.stderr)
            sys.exit(10)

    # Print the XML representation
    program.write(sys.stdout.buffer, encoding='UTF-8', xml_declaration=True)
