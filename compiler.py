import ast
from pathlib import Path
from pprint import pprint
import operator as ops

from helpclasses import NameLocations

global DEBUG
DEBUG = True

class Compiler:
    """
    Class to compile Python code into AQA Assembly (see README.md).
    Compiled code is stored in self.compiled.
    Currently compiles code in ./test_code.py and the compiled code is available upon instantiation.
    """#TODO: allow caller to change the source code that is compiled - perhaps use __call__ to return self.compiled or write it out?
    def __init__(self):
        self.TEST_FILE = Path("./test_code.py")

        #TODO: memory management for when we run out of registers
        self.REGISTERS = NameLocations(max_size=12, name="REGISTERS")
        self.MEM_LOCATIONS = NameLocations(max_size=975, name="MAIN MEMORY")# 975 = 5*195

        self.temp_reg_counter = 0
        self.branch_counter = {x: 0 for x in "whiletest, whilebody, endwhile, for, if, elif, else, endif, mul, div".split(", ")} # some for later
        self.COMP_OPS = {ast.Gt: ops.gt, ast.Lt: ops.lt, ast.Eq: ops.eq, ast.NotEq: ops.ne, ast.GtE: ops.ge, ast.LtE: ops.le}

        asty = self.get_ast()
        if DEBUG:
            pprint(ast.dump(asty))
        self.compiled = ""
        self.compile_ast(asty)
        self.compiled += "\nHALT"        
        
    def get_ast(self) -> ast.Module:
        "Returns an Abstract Syntax Tree of the Python code in self.TEST_FILE."
        with open(self.TEST_FILE, mode="r", encoding="utf8") as tf:
            return ast.parse(tf.read(), self.TEST_FILE, "exec")
                
    def compile_ast(self, ast_: ast.Module or list) -> None: #TODO: strings, BIDM-AS-, for-loops (convert to while then compile?)
        "Compiles an Abstract Syntax Tree, or a list of its nodes into AQA Assembly."
        if hasattr(ast_, "body"):
            body = ast_.body
        else:
            body = ast_
        for stmt in body:
            if DEBUG:
                print(ast.dump(stmt))
            #pprint(self.REGISTERS) #TODO: R1 is not 
            if isinstance(stmt, ast.Assign): # <x> = <y>, <z>
                self.compile_Assign(stmt)
            elif isinstance (stmt, ast.AugAssign): # <x> <op>= <y> -> <x> = <x> <op> <y>
                self.compile_AugAssign(stmt)
            elif isinstance(stmt, ast.While): # while <test>: <body>
                self.compile_While(stmt)
            elif isinstance(stmt, ast.If):
                self.compile_If(stmt)
            pprint(self.REGISTERS) 

    def compile_Assign(self, assign: ast.Assign) -> None:
        "Compiles statements of the type `spam = ham`."
        for t in assign.targets:
            if isinstance(assign.value, ast.BinOp):
                self.compile_BinOp(assign.value, t.id)
            else:
                reg = self.set_register(t.id) 
                self.compiled += f"MOV R{reg}, "
                if isinstance(assign.value, ast.Num):
                    self.compiled += "#" + str(assign.value.n)
                self.compiled += "\n"

    def compile_AugAssign(self, assign: ast.AugAssign) -> None:
        "Compiles statements of the type `spam += ham`."
        temp_assign = ast.Assign(targets = [assign.target],
                                 value = ast.BinOp(
                                     left = assign.target,
                                     op = assign.op,
                                     right = assign.value
                                     )
                                 )
        self.compile_Assign(temp_assign)

    def compile_BinOp(self, stmt: ast.BinOp, dest: str) -> None:
        """
        Compiles statements of the type `spam + ham` and places them into `dest`.
        TODO: multiplication and division.
        """
        left_reg = self.get_register(stmt.left)
        if isinstance(stmt.right, ast.Constant):
            if not isinstance(stmt.right.value, int):
                raise TypeError("py2aqa32 only supports integer constants.")
            right = "#" + str(stmt.right.value)
        else:
            right = "R" + str(self.get_register(stmt.right))
        pprint(self.REGISTERS)
        dest_reg = self.set_register(dest)            
        #ops = {ast.Add: "ADD", ast.Sub: "SUB"}
        if isinstance(stmt.op, ast.Add):
            self.compiled += "ADD "
        elif isinstance(stmt.op, ast.Sub):
            self.compiled += "SUB "
        self.compiled += f"R{dest_reg}, R{left_reg}, {right}\n"

    def compile_While(self, stmt: ast.While) -> None:
        """
        A While loop is a block of code and three branches.

        Three branches are needed to prevent the loop becoming a do-while loop:
            - one at the start which branches to while loop's body (label: 'whilebody') if its test is passed.
            - one after that but before 'whilebody' which branches to the label 'endwhile'.
                - this is run if the while loop has finished.
            - one at the end which returns to the first branch (label: 'whiletest').
        
        A comparision may be done between two constants.
        In that case, the compile tests them before compilation and and does not include the while loop if the comparision is patently false.
        A constant can also be the "test" of a while loop: the same principle applies.
        If the constant is truey an unconditional branch is used.
        This does not affect variables defined in the loop as they should be destroyed by scope anyway.

        'endwhile' is guarenteed to come after the entire while loop and is a return to the main code.      
        """ #TODO: implement memory management and call it at endwhile.
        test_label, body_label, end_label = self.get_label("whiletest"), self.get_label("whilebody"), self.get_label("endwhile")
        test = self._compile_test_to_str(stmt.test, body_label)
        if test is None: # could return None with a Const == Const where the statement is patently false
            return None # no need to compile a null-condition
        self._compile_label(test_label)
        self.compiled += test # must include a branch
        self.compiled += f"B {end_label}\n" # if the test was false we must skip to the end.
        self._compile_label(body_label)
        self.compile_ast(stmt.body) 
        self.compiled += f"B {test_label}\n"
        self._compile_label(end_label) # must be the final statement

    def compile_If(self, stmt: ast.If) -> None: #TODO: elif, else
        """
        An If statement is a non-recursive series of branches each leading to a block of code.

        Like in self.compile_While, if a test is patently false that entire block is removed from the code.
        Unconditional branches are used for patently/constantly true tests, e.g. `if True:`.

        Note that ast records elif as another instance of ast.If but stored in the `orelse` block not the `body` block.
        This method must therefore be recursive.

        compile_If uses the `if` and `endif`, and often `elif` (not recursive?) and `else` too.
        `endif` is used in an else-free statement to skip past the if-block.
        `endif` is used in an else-full statement at the end of each if/elif-block to skip past the over blocks.
        `endif` refers to the statement after the entire if statement (i.e. all of if/elif/else).
        """
        if_label = self.get_label("if")
        endif_label = self.get_label("endif")
        test = self._compile_test_to_str(stmt.test, if_label)
        if test is None:
            return None
        self.compiled += test
        if len(stmt.orelse) == 0: # perhaps this should be a flag?
            self.compiled += f"B {endif_label}\n" # in case there is no else
        # insert elif/else etc here.
        self._compile_label(if_label)
        self.compile_ast(stmt.body)
        self._compile_label(endif_label) # must be the final statement

    def _compile_test_to_str(self, test: ast.Compare or ast.Constant, label: str) -> str or None:
        """
        Compiles a test as used by If and While. Returns the assembly code to be used by If or While.
        This assembly code always includes a branch to `label`.
        """
        if isinstance(test, ast.Constant):
            if not test.value:
                return None # if the constant is falsey the while-loop will never run.
            return f"B {label}\n"
        else:
            if len(test.ops) > 1 or len(test.comparators) > 1:
                raise NotImplementedError("Multiple comparisons.") 
            left = test.left
            right = test.comparators[0]
            op = test.ops[0]
            if isinstance(left, ast.Constant) and isinstance(right, ast.Constant): # optimise out Const == Const
                comp = self.COMP_OPS[type(op)]
                if comp(left.value, right.value):
                    return self._compile_test_to_str(test=ast.Constant(value=True), label=label)
            else:
                left_r = self.get_register(left)
                right_r = self.get_register(right)
                return self._compile_condition_to_str(left_r, right_r, op, label)

    def _compile_condition_to_str(self, left_reg: int, right_reg: int, op, true_label: str) -> str: # may need revising for elif/else etc
        "Compiles statements into a CMP followed by one or more conditional branches, depending on `op`."
        #NB: order of left_reg and right_reg is same in Python and real life.
        compiled = f"CMP R{left_reg}, R{right_reg}\n"
        if isinstance(op, ast.Eq):
            compiled += f"BEQ {true_label}"
        elif isinstance(op, ast.NotEq):
            compiled += f"BNE {true_label}"
        elif isinstance(op, ast.Lt):
            compiled += f"BLT {true_label}"
        elif isinstance(op, ast.LtE):
            compiled += f"BLT {true_label}"
            compiled += f"BEQ {true_label}"
        elif isinstance(op, ast.Gt):
            compiled += f"BGT {true_label}"
        elif isinstance(op, ast.GtE):
            compiled += f"BGT {true_label}"
            compiled += f"BEQ {true_label}"
        else:
            raise NotImplementedError(f"This comparison operator: \n{op}.")
        compiled += "\n"
        return compiled

    def _compile_label(self, label: str) -> None: # in case it changes
        "Adds a label + a colon + a new line into the assembly."
        self.compiled += label + ":\n"

    def get_label(self, keyword: str) -> str:
        """
        Returns the next label for this keywords.
        Labels start at 0 - the counter is `self.branch_counter`.
        """
        label = keyword + str(self.branch_counter[keyword])
        self.branch_counter[keyword] += 1
        return label

    def get_register(self, var: ast.Name or ast.Constant) -> int:
        """
        Returns the register that `var` is registered to. 
        If `var` is a constant the constant is assigned a register and that is returned.
        """
        if isinstance(var, ast.Name):
            r = self.get_register_from_name(var.id)
        elif isinstance(var, ast.Constant): # perhaps look for constants already stored?
            # originally this raised a ValueError for reasons forgotten - may have been laziness
            r = self.give_constant_register(var.value)[1]
        return r
    
    def get_register_from_name(self, name: str) -> int:
        """
        Returns the register that a variable name is registered to.
        If the variable is in memory, but not in the registers, then a `LDR` call is added to `self.compiled`.
        """
        if name in self.REGISTERS:
            return self.REGISTERS[name]
        elif name in self.MEM_LOCATIONS:
            memloc = self.MEM_LOCATIONS[name]
            r = self.set_register(name)
            self.compiled += f"LDR R{r}, {memloc}\n"
            return r
        else:
            raise NameError(f"name '{name}' is not defined.")

    #TODO: investigate whether this causes an issue with while-loop scope.
    # currently this is added to self.compiled before the whiletest label
    # - which is more optimal but could mean it's overwritten
    #TODO: call constants `constx` where x is their value and look them up before assigning a new register.
    def give_constant_register(self, value: int) -> str and int:
        "Assigns a register to a constant and returns the temporary name and the register."
        if not isinstance(value, int):
            raise TypeError("py2aqa32 only supports integer constants.") 
        name = "const" + str(self.temp_reg_counter)
        self.temp_reg_counter += 1
        r = self.set_register(name)
        self.compiled += f"MOV R{r}, #{value}\n"
        return name, r

    def set_register(self, name: str) -> int:
        "Assigns a register to a variable name and returns that register."
        #if DEBUG:
         #   pprint((name, self.REGISTERS))
        if name in self.REGISTERS.keys():
            return self.get_register_from_name(name)
        if DEBUG:
            pprint((name, self.REGISTERS))
        reg = self.REGISTERS.find_first_empty_loc()
        self.REGISTERS[name] = reg
        if DEBUG:
            # Comment to help the reader/tester understand the output.
            self.compiled += f"\n//{name} = R{reg}\n"
        return reg 

if __name__ == "__main__":
    c = Compiler()
    print(c.compiled)
    if DEBUG:
        input("Press enter to exit.")
