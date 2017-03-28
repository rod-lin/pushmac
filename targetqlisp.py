import sys
from rpython.rlib.parsing.tree import Nonterminal, Symbol, RPythonVisitor
from rpython.rlib.parsing.parsing import PackratParser, Symbol, ParseError, Rule
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

class QLExpr:
	def __init__():


class QLParser:
	regexs, rules, transformer = parse_ebnf("""
		IGNORE: " ";
		
		TNUM: "(0|[1-9][0-9]*)(\.[0-9]+)?";

		call: expr | expr call;

		number: TNUM;
		primary: number | id;

		expr: call | primary | "(" expr ")";
	""")

	fparse = make_parse_function(regexs, rules)

	def __init__(): pass

	class _Visitor: pass

	def parse(src):
		tree = fparse(src)

def main(argv): pass

def target(driver, args):
	driver.exe_name = "pushmac-%(backend)s"
	return main

if __name__ == '__main__':
	sys.exit(main(sys.argv))
