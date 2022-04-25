
import ast
from pathlib import Path
from pprint import pprint
import operator as ops

from helpclasses import NameLocations

global DEBUG
DEBUG = True

class Compiler:

    def __init__(self):
        self.TEST_FILE = Path("./test_code.py")

        self.REGISTERS = NameLocations(max_size=12, name="REGISTERS")
        self.MEM_LOCATIONS = NameLocations(max_size=975, name="MAIN MEMORY")# 975 = 5*195

        self.temp_reg_counter = 0
        self.loop_counter = {"while": 0, "for": 0,"mul": 0, "div": 0} # some for later

        asty = self.get_ast()
        if DEBUG:
            pprint(ast.dump(asty))
        self.compiled = ""
        self.compile_ast(asty)
        self.compiled += "\nHALT"        
        
    def get_ast(self):
        with open(self.TEST_FILE, mode="r", encoding="utf8") as tf:
            return ast.parse(tf.read(), self.TEST_FILE, "exec")
                
    def compile_ast(self, ast_): #TODO: strings, BIDM-AS-, for-loops (convert to while then compile?)
        for stmt in ast_.body:
            if DEBUG:
                print(ast.dump(stmt))
            #pprint(self.REGISTERS) #TODO: R1 is not 
            if isinstance(stmt, ast.Assign): # <x> = <y>, <z>
                self.compile_Assign(stmt)
            elif isinstance (stmt, ast.AugAssign): # <x> <op>= <y> -> <x> = <x> <op> <y>
                temp_assign = ast.Assign(targets = [stmt.target],
                                         value = ast.BinOp(
                                             left = stmt.target,
                                             op = stmt.op,
                                             right = stmt.value
                                             )
                                         )
                self.compile_Assign(temp_assign)
            elif isinstance(stmt, ast.While): # while <test>: <body>
                self.compile_While(stmt)
            pprint(self.REGISTERS) 

    def compile_Assign(self, assign):
        for t in assign.targets:
            if isinstance(assign.value, ast.BinOp):
                self.compile_BinOp(assign.value, t.id)
            else:
                reg = self.set_register(t.id) 
                self.compiled += f"MOV R{reg}, "
                if isinstance(assign.value, ast.Num):
                    self.compiled += "#" + str(assign.value.n)
                self.compiled += "\n"

    def compile_BinOp(self, stmt, dest):
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

    def compile_While(self, stmt):
        if isinstance(stmt.test, ast.Constant):
            if not stmt.test.value:
                return None # if the constant is falsey the while-loop will never run.
            label = self.get_label("while")
            self.compiled += "\n" + label + ": " # \n just in case
            self.compile_ast(stmt) # shouldn't recurse as there this method will look at the while loop's body
            self.compiled += f"B {label}\n"
            return None
        else:
            return self.compile_While_conditional(stmt)
                        
    def compile_While_conditional(self, stmt):          
        test = stmt.test
        if isinstance(test, ast.Compare): # can this be assumed?
            if len(test.ops) > 1 or len(test.comparators) > 1:
                raise NotImplementedError("Multiple comparisons.")
            if isinstance(test.left, ast.Constant) and isinstance(test.right, ast.Constant): # optimise out Const == Const
                comps = {ast.Gt: ops.gt, ast.Lt: ops.lt, ast.Eq: ops.eq, ast.Ne: ops.ne, ast.Ge: ops.ge, ast.Le: ops.le}
                op = ops[0]
                comp = comps[type(op)]
                if comp(test.left.value, test.right.value):
                    new_while = ast.While(test=Constant(value=True), body=stmt.body, orelse=stmt.orelse)
                    return self.compile_While(new_while)
            
                    
    def get_label(self, keyword):
        label = keyword + str(self.loop_counter[keyword])
        self.loop_counter[keyword] += 1
        return label

    def get_register(self, var):
        if isinstance(var, ast.Name):
            r = self.get_register_from_name(var.id)
        elif isinstance(var, ast.Constant): # perhaps look for constants already stored?
            raise ValueError("Constant has no register.")
        return r
    
    def get_register_from_name(self, name):
        if name in self.REGISTERS:
            return self.REGISTERS[name]
        elif name in self.MEM_LOCATIONS:
            memloc = self.MEM_LOCATIONS[name]
            r = self.set_register(name)
            self.compiled += f"LDR R{r}, {memloc}\n"
            return r
        else:
            raise NameError(f"name '{name}' is not defined.")

    def set_register(self, name):
        #if DEBUG:
         #   pprint((name, self.REGISTERS))
        if name in self.REGISTERS.keys():
            return self.get_register_from_name(name)
        if DEBUG:
            pprint((name, self.REGISTERS))
        reg = self.REGISTERS.find_first_empty_loc()
        self.REGISTERS[name] = reg
        return reg 

if __name__ == "__main__":
    c = Compiler()
    print(c.compiled)
    if DEBUG:
        input("Press enter to exit.")
