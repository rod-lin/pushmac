# push machine 0.0

# push 1
# print
# set $1 2
# 

import re
import sys
from rpython.rlib import jit

pmac_bytecode = [ "ldi", "pop", "out", "add", "jmp", "jt", "lt", "eq", "not", "set", "get" ]
pmac_bytecode = { name: i for i, name in enumerate(pmac_bytecode) }
for k, v in pmac_bytecode.items():
	globals()["pmac_bytecode_" + k] = v

def err(msg):
	print("error: " + msg)
	raise Exception(msg)

def splitx(src, char = [ " ", "\t", "\n", "\r" ]):
	ret = []
	beg = 0

	for i in range(len(src)):
		if src[i] in char:
			ret.append(src[beg:i].strip())
			beg = i + 1

	ret.append(src[beg:].strip())

	return [ a for a in ret if len(a) ]

def isint(src):
	try:
		int(src)
		return 1
	except:
		return 0

str_pool = []

def reg_str(s):
	str_pool.append(s)
	return len(str_pool) - 1

def get_str(i):
	return str_pool[i]

def parse(src):
	# instr = { "ldi": , "pop", "out" }
	
	"""
	return map(
		lambda l:
			[ pmac_bytecode[l[0].lower()] ] +
			map(lambda arg:
				int(arg) if re.match(r"0|([1-9][0-9]*)", arg)
				else err("illegal argument '%s'" % arg), l[1:]),
		map(
			lambda l: l.split(),
			filter(
				lambda l: 1 if len(l) else 0,
				map(
					lambda l: l.strip(),
					re.split(r"\r|\n", src)
				)
			)
		)
	)
	"""

	ret = splitx(src, [ "\r", "\n" ])
	ret = [ splitx(l) for l in ret ]
	ret = [ [ pmac_bytecode[l[0].lower()] ] + ([ int(arg) if isint(arg) else reg_str(arg) for arg in l[1:] ] if len(l) > 1 else []) for l in ret ]

	return ret

driver = jit.JitDriver(greens = [ "pc", "bc" ], reds = "auto")

def _rt_check_stack(sp, req, msg = "insufficient stack"):
	if sp < req:
		err(msg)

def run(bc):
	pc = 0
	stack = [ 0 ] * 1024
	sp = 0
	ins = None
	glob = {}

	while pc < len(bc):
		driver.jit_merge_point(pc = pc, bc = bc)

		ins = bc[pc]

		if ins[0] == pmac_bytecode_ldi:
			stack[sp] = ins[1]
			sp += 1

		elif ins[0] == pmac_bytecode_pop:
			_rt_check_stack(sp, 1)
			sp -= 1

		elif ins[0] == pmac_bytecode_out:
			_rt_check_stack(sp, 1)
			print(stack[sp - 1])

		elif ins[0] == pmac_bytecode_add:
			_rt_check_stack(sp, 2)
			stack[sp - 2] = stack[sp - 2] + stack[sp - 1]
			sp -= 1

		elif ins[0] == pmac_bytecode_jmp:
			pc += ins[1]
			continue

		# jump if true
		elif ins[0] == pmac_bytecode_jt:
			_rt_check_stack(sp, 1)
			sp -= 1
			if stack[sp]:
				pc += ins[1]
				continue

		elif ins[0] == pmac_bytecode_lt:
			_rt_check_stack(sp, 2)
			stack[sp - 2] = stack[sp - 2] < stack[sp - 1]
			sp -= 1

		elif ins[0] == pmac_bytecode_eq:
			_rt_check_stack(sp, 2)
			stack[sp - 2] = stack[sp - 2] == stack[sp - 1]
			sp -= 1

		elif ins[0] == pmac_bytecode_not:
			_rt_check_stack(sp, 1)
			stack[sp - 1] = not stack[sp - 1]

		elif ins[0] == pmac_bytecode_set:
			_rt_check_stack(sp, 1)
			glob[get_str(ins[1])] = stack[sp - 1]
			sp -= 1

		elif ins[0] == pmac_bytecode_get:
			stack[sp] = glob[get_str(ins[1])]
			sp += 1

		pc += 1

def main(argv):
	if len(argv) < 2:
		print("push machine 0.0: input a file")
		return 1

	file = open(argv[1])
	src = file.read()
	file.close()

	bc = parse(src)
	print(bc)
	run(bc)

	return 0


# pypy interfaces

def target(driver, args):
	driver.exe_name = "pushmac-%(backend)s"
	return main

def jitpolicy(driver):
	from rpython.jit.codewriter.policy import JitPolicy
	return JitPolicy()

if __name__ == '__main__':
	sys.exit(main(sys.argv))
