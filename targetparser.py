import sys
from rpython.rlib.parsing.tree import Nonterminal, Symbol, RPythonVisitor
from rpython.rlib.parsing.parsing import PackratParser, Symbol, ParseError, Rule
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

def main(argv):
	regexs, rules, transformer = parse_ebnf("""
		IGNORE: " ";
		DECIMAL: "(0|[1-9][0-9]*)(\.[0-9]+)?";
	
		additive: multitive "+" additive | multitive "-" additive | multitive;
		multitive: primary "*" multitive | primary "/" multitive | primary;
		number: DECIMAL;
		primary: number | "(" additive ")";
	""")

	class Visitor(object):
		def visit_number(self, node):
			print(node.children[0].additional_info)
			return float(node.children[0].additional_info)

		def visit_additive(self, node):
			if len(node.children) == 1:
				return node.children[0].visit(self)
			elif node.children[1].additional_info == "+":
				return node.children[0].visit(self) + node.children[2].visit(self)
			elif node.children[1].additional_info == "-":
				return node.children[0].visit(self) - node.children[2].visit(self)
	
		def visit_multitive(self, node):
			if len(node.children) == 1:
				return node.children[0].visit(self)
			elif node.children[1].additional_info == "*":
				return node.children[0].visit(self) * node.children[2].visit(self)
			elif node.children[1].additional_info == "/":
				return node.children[0].visit(self) / node.children[2].visit(self)

		def visit_primary(self, node):
			if len(node.children) == 3:
				return node.children[1].visit(self)
			else:
				return node.children[0].visit(self)
	
	parse = make_parse_function(regexs, rules)
	tree = parse("999 / 3.2 + 2")
	print(tree.visit(Visitor()))

def target(driver, args):
	driver.exe_name = "pushmac-%(backend)s"
	return main

if __name__ == '__main__':
	sys.exit(main(sys.argv))
