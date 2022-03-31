import ast
from pathlib import Path
from pprint import pprint
from helpclasses import NameLocations

global DEBUG
DEBUG = True

class Compiler:

    def __init__(self):
        self.TEST_FILE = Path("./test_code.py")
        self.REGISTERS = NameLocations(max_size=12, name="REGISTERS")
        self.MEM_LOCATIONS = NameLocations(max_size=975, name="MAIN MEMORY")# 975 = 5*195
        asty = self.get_ast()
        if DEBUG:
            pprint(ast.dump(asty))
        self.compiled = ""
        self.compile_ast(asty)
        
    def get_ast(self):
        with open(self.TEST_FILE, mode="r", encoding="utf8") as tf:
            return ast.parse(tf.read(), self.TEST_FILE, "exec")
                
    def compile_ast(self, ast_):
        for stmt in ast_.body:
            if isinstance(stmt, ast.Assign):
                for t in stmt.targets:
                    reg = self.set_register(t.id) 
                    if isinstance(stmt.value, ast.BinOp):
                        self.compile_BinOp(stmt.value, t.id)
                    else:
                        self.compiled += f"MOV R{reg}, "
                        if isinstance(stmt.value, ast.Num):
                            self.compiled += "#" + str(stmt.value.n)
                        # what about strings?
                        self.compiled += "\n"

    def compile_BinOp(self, stmt, dest):
        left_reg = self.get_register(stmt.left.id)
        right_reg = self.get_register(stmt.right.id)
        dest_reg = self.set_register(dest)            
        ops = {ast.Add: "ADD", ast.Sub: "SUB"}
        if isinstance(stmt.op, ast.Add):
            self.compiled += "ADD "
        elif isinstance(stmt.op, ast.Sub):
            self.compiled += "SUB "
        self.compiled += f"R{dest_reg}, R{left_reg}, R{right_reg}\n"
    
    def get_register(self, name):
        if name in self.REGISTERS:
            return self.REGISTERS[name]
        elif name in self.MEM_LOCATIONS:
            memloc = self.MEM_LOCATIONS[name]
            r = self.REGISTERS.find_first_empty_loc()
            self.REGISTERS[name] = r
            self.compiled += f"LDR R{r}, {memloc}\n"
            return r
        else:
            raise NameError(f"name '{name}' is not defined.")

    def set_register(self, name):
        reg = self.REGISTERS.find_first_empty_loc()
        self.REGISTERS[name] = reg
        return reg
    



if __name__ == "__main__":
    c = Compiler()
    print(c.compiled)
    input("Press enter to exit.")
