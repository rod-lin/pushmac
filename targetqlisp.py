import sys
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function

class QLSingle(object):
	objs = {}
	def __new__(cls):
		if cls in cls.objs:
			return cls.objs[cls]

		obj = object.__new__(cls)
		cls.objs[cls] = obj
		return obj

class QLExc(Exception): pass
class QLExcNoOp(QLExc): pass

### > Object

class QLObj(object):
	def __init__(self, tname = "object"):
		self.slots = {}
		self.tname = tname

	def __str__(self):
		return "<q %s at %s>" % (self.tname, hex(id(self)))

	def sets(self, slot, obj):
		self.slots[slot] = obj
		return obj

	def gets(self, slot):
		return self.slots[slot] if slot in self.slots else None

	def dels(self, slot):
		if slot in self.slots:
			obj = self.slots[slot]
			del self.slots[slot]
			return obj
		return None

	def type(self):
		return self.tname

class QLObjNone(QLObj, QLSingle):
	def __init__(self):
		QLObj.__init__(self, "none")

class QLObjNumber(QLObj):
	def __init__(self, num):
		QLObj.__init__(self, "number")
		self.val = num

	def __str__(self):
		return str(self.val)

	def add(self, obj):
		t = type(obj)

		if t == QLObjNumber:
			return QLObjNumber(self.val + obj.val)

		raise QLExcNoOp("unsupported op")

class QLObjFunction(QLObj):
	def __init__(self, body):
		QLObj.__init__(self, "function")
		self.body = body

	def call(self, ctx, args):
		nctx = QLContext(ctx)

		for i, arg in enumerate(args):
			# args are evaluated here
			nctx.sets("$" + i, arg.eval(ctx))

		return self.body.eval(nctx)

class QLObjNativeFunction(QLObj):
	def __init__(self, proc):
		QLObj.__init__(self, "native function")
		self.proc = proc

	def call(self, ctx, args):
		return self.proc(ctx, args)

	@staticmethod
	def nat_add(ctx, args):
		if len(args) == 0: return QLObjNone()

		acc = args[0].eval(ctx)

		for arg in args[1:]:
			acc = acc.add(arg.eval(ctx))

		return acc

class QLContext(QLObj):
	def __init__(self, prev):
		QLObj.__init__(self, "context")
		self.prev = prev
		self.tab = {}

	def search(self, slot):
		ret = self.gets(slot)

		if not ret is None:
			return ret

		if not self.prev is None:
			return self.prev.search(slot)

		return None

### < Object

### > Expression

class QLExpr(object):
	def __init__(self): pass
	# def eval(self, ctx)

class QLExprID(QLExpr):
	def __init__(self, id):
		QLExpr.__init__(self)
		self.id = id

	def eval(self, ctx):
		obj = ctx.search(self.id)

		if obj is None:
			return QLObjNone()

		return obj

class QLExprNumber(QLExpr):
	def __init__(self, val):
		QLExpr.__init__(self)
		self.val = float(val)

	def eval(self, ctx):
		return QLObjNumber(self.val)

class QLExprCall(QLExpr):
	def __init__(self, fn, args):
		QLExpr.__init__(self)
		self.fn = fn
		self.args = args

	def eval(self, ctx):
		fn = self.fn.eval(ctx)
		return fn.call(ctx, self.args)

### < Expression

class QLAST:
	def __init__(self, tree):
		self.tree = tree

	class _Visitor:
		def visit_call(self, node):
			fn = node.children[1].visit(self)
			args = []

			child = node.children[2]

			while 1:
				args.append(child.children[0].visit(self))
				if len(child.children) > 1:
					child = child.children[1]
				else: break

			return QLExprCall(fn, args)

		def visit_id(self, node):
			return QLExprID(node.children[0].additional_info)

		def visit_number(self, node):
			return QLExprNumber(node.children[0].additional_info)

		def visit_primary(self, node):
			return node.children[0].visit(self)

		def visit_expr(self, node):
			l = len(node.children)

			if l == 1:
				return node.children[0].visit(self)
			elif l == 3: # (expr)
				return node.children[1].visit(self)

			raise Exception("unexpected children len")

	# generate expression
	def gen(self):
		return self.tree.visit(QLAST._Visitor())

class QLParser:
	regexs, rules, transformer = parse_ebnf("""
		IGNORE: "\s";
		
		TNUM: "(0|[1-9][0-9]*)(\.[0-9]+)?";
		TID: "[^\\(\\)\\s]+";

		expr: call | primary;

		id: TID;
		number: TNUM;
		primary: number | id;

		call: "(" expr (expr)* ")";
	""")

	def __init__(self): pass

	def parse(self, src):
		fparse = make_parse_function(QLParser.regexs, QLParser.rules)
		tree = fparse(src)
		return QLAST(tree)

def main(argv):
	parser = QLParser()
	ast = parser.parse("(+\t3 2)")
	toplev = ast.gen()

	glob = QLContext(None)

	nf = QLObjNativeFunction(QLObjNativeFunction.nat_add)
	glob.sets("+", nf)

	val = toplev.eval(glob)

	print(val)

def target(driver, args):
	driver.exe_name = "pushmac-%(backend)s"
	return main

if __name__ == '__main__':
	sys.exit(main(sys.argv))
