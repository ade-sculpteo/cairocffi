# coding: utf8
import re
import pycparser.c_generator
import cffi


class Visitor(pycparser.c_ast.NodeVisitor):

    def __init__(self):
        pycparser.c_ast.NodeVisitor.__init__(self)
        self.enums = []

    def visit_Typedef(self, node):
        if isinstance(node.type.type, pycparser.c_ast.Enum):
            self.enums.append(node.name)


def generate(include_dir):
    # Remove comments, preprocessor instructions and macros.
    source = re.sub(
        b'/\*.*?\*/'
        b'|CAIRO_(BEGIN|END)_DECLS'
        b'|cairo_public '
        br'|^\s*#.*?[^\\]\n',
        b'',
        b''.join(open('%s/cairo%s.h' % (include_dir, suffix), 'rb').read()
                 for suffix in ['', '-pdf', '-ps', '-svg']),
        flags=re.DOTALL | re.MULTILINE)
    print('# Generated by mkconstants.py\n')

    ast = pycparser.CParser().parse(source)
    source = pycparser.c_generator.CGenerator().visit(ast)

    visitor = Visitor()
    visitor.visit(ast)
    enums = visitor.enums

    ffi = cffi.FFI()
    ffi.cdef(source)

    for enum_type in sorted(enums):
        for value, name in sorted(ffi.typeof(enum_type).elements.items()):
            if name.startswith("CAIRO_"):
                name = name[6:]
            print('%s = %r' % (name, value))
        print('')

    print('_CAIRO_HEADERS = r"""\n%s\n"""' % source.strip())


if __name__ == '__main__':
    generate('/usr/include/cairo')
