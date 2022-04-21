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
        self.temp_reg_counter = 0
        asty = self.get_ast()
        if DEBUG:
            pprint(ast.dump(asty))
        self.compiled = ""
        self.compile_ast(asty)        
        
    def get_ast(self):
        with open(self.TEST_FILE, mode="r", encoding="utf8") as tf:
            return ast.parse(tf.read(), self.TEST_FILE, "exec")
                
    def compile_ast(self, ast_): #TODO: strings, BIDM-AS-, for-loops (convert to while then compile?)
        for stmt in ast_.body:
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
        self.compiled += "\nHALT"

    def compile_Assign(self, assign):
        for t in assign.targets:
            reg = self.set_register(t.id) 
            if isinstance(assign.value, ast.BinOp):
                self.compile_BinOp(assign.value, t.id)
            else:
                self.compiled += f"MOV R{reg}, "
                if isinstance(assign.value, ast.Num):
                    self.compiled += "#" + str(assign.value.n)
                self.compiled += "\n"

    def compile_BinOp(self, stmt, dest):
        left_reg = self.get_register(stmt.left)
        right_reg = self.get_register(stmt.right)
        dest_reg = self.set_register(dest)            
        ops = {ast.Add: "ADD", ast.Sub: "SUB"}
        if isinstance(stmt.op, ast.Add):
            self.compiled += "ADD "
        elif isinstance(stmt.op, ast.Sub):
            self.compiled += "SUB "
        self.compiled += f"R{dest_reg}, R{left_reg}, R{right_reg}\n"

    def get_register(self, var):
        if isinstance(var, ast.Name):
            r = self.get_register_from_name(var.id)
        elif isinstance(var, ast.Constant): # perhaps look for constants already stored?
            if not isinstance(var.value, int): 
                raise TypeError("py2aqa32 only supports integer constants.")
            r = self.set_register("temp" + str(self.temp_reg_counter))
            self.temp_reg_counter += 1
            self.compiled += f"MOV R{r}, #{var.value}\n"
        return r
    
    def get_register_from_name(self, name):
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
    if DEBUG:
        input("Press enter to exit.")
