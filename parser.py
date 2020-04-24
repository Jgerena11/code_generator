from scanner import *
import sys


class Parser:

    class CodeGen:
        count = 1
        temp_var = 0
        bp_stack = []
        code = {}
        bpw = []
        bpw_flag = False
        bpo = []
        bpo_flag = False
        bpe = []
        bpe_flag = False
        block = []

        def add_code(self, quad):
            if self.bpw_flag:
                quad.append('bpw= ' + str(self.count))
                self.code.update({str(self.count): quad})
                self.bpw_flag = False
            elif self.bpo_flag:
                quad.append('loc for bpo')
                self.code.update({str(self.count): quad})
                self.bpo_flag = False
            elif self.bpe_flag:
                quad.append('val for bpe')
                self.code.update({str(self.count): quad})
                self.bpe_flag = False
            else:
                self.code.update({str(self.count): quad})
            self.count += 1

        def print_quadruples(self):
            for i in range(1, self.count):
                print(str(i), end="\t")
                for string in self.code[str(i)]:
                    string = string + ' '
                    print(string, end="\t")
                print('\n', end='')

        def temp(self):
            t = self.temp_var
            self.temp_var += 1
            return str('_t'+str(t))

        # ---- bpe functions --------
        def bpe_push(self):
            n = self.count
            self.bpe.append(n)
            return n

        # ---- bpw functions -----------
        def bpw_push(self):
            n = self.count
            self.bpw.append(n)
            self.bpw_flag = True
            return n

        def bpw_pop(self):
            n = self.bpw.pop()
            return n

        # ---- bpo functions -----------
        def bpo_push(self):
            n = self.count
            self.bpo.append(n)
            return n

        def back_patch_o(self):
            n = self.bpo.pop()
            self.bpo_flag = True
            self.code[str(n)][3] = str(self.count)
            return n

        def push_block(self):
            if self.code[str(self.count - 1)][0] != 'func' and self.code[str(self.count - 1)][0] != 'param':
                if self.code[str(self.count - 2)][0] != 'param':
                    self.add_code(['block', '\t', '\t', '\t'])
                    self.block.append('{')

        def pop_block(self):
            if len(self.block) > 0:
                self.block.pop()
                self.add_code(['end', 'block', '\t', '\t'])
                return True
            else:
                return False

        def back_patch_e(self):
            if len(self.bpe) > 0:
                n = self.bpe.pop()
                self.code[str(n)][3] = str(self.count)
                return n

    gen = CodeGen()

    var_declaration_first = [';', '[']
    type_specifier_first = ['int', 'void']
    compound_stmt_first = ['{']
    factor_first = ['(', 'ID', 'NUM']
    expression_stmt_first = ['(', 'ID', 'NUM', ';']
    expression_first = ['(', 'ID', 'NUM']
    expression_double_prime_first = ['=', '*', '/', '+', '-', '<=', '>', '<', '>=', '==', '!=']
    statement_first = ['(', 'ID', 'NUM', ';', 'if', 'while', 'return', '{']

    count = 0
    result = True

    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = tokens[self.count]

    def accept(self, token):
        self.count += 1
        self.current_token = self.tokens[self.count]

    def program(self):
        self.declaration_list()
        self.gen.print_quadruples()
        if self.current_token.type == '$':
            return
        else:
            self.result = False

    def declaration_list(self):
        self.declaration()
        self.declaration_list_prime()

    def declaration_list_prime(self):
        if self.current_token.type in ['int', 'void']:
            self.declaration()
            self.declaration_list_prime()

    def type_specifier(self):
        if self.current_token.type in ['int', 'void']:
            type_spec = self.current_token.value
            self.accept(self.current_token)
            return type_spec
        else:
            self.result = False

    def declaration(self):
        type_spec = self.type_specifier()
        if self.current_token.type == 'ID':
            dec_id = self.current_token.value
            self.accept(self.current_token)
            self.declaration_prime(type_spec, dec_id)
        else:
            self.result = False

    def var_declaration(self, type_spec, dec_id):
        if self.current_token.type == ';':
            self.accept(';')
            self.gen.add_code(['alloc', '4', '\t', dec_id])
            return
        elif self.current_token.type == '[':
            self.accept('[')
            if self.current_token.type == 'NUM':
                number = int(self.current_token.value)
                self.accept('NUM')
                self.gen.add_code(['alloc', str(4 * number), '\t', dec_id])
                if self.current_token.type == ']':
                    self.accept(']')
                    if self.current_token.type == ';':
                        self.accept(';')
                        return
        self.result = False

    def statement_list(self):
        if self.current_token.type in self.statement_first:
            self.statement()
            self.statement_list()

    def local_declarations(self):
        if self.current_token.type in ['int', 'void']:
            type_spec = self.current_token.value
            self.accept(self.current_token)
            if self.current_token.type == 'ID':
                dec_id = self.current_token.value
                self.accept('ID')
                self.var_declaration(type_spec, dec_id)
                self.local_declarations()

    def compound_stmt(self):
        if self.current_token.type == '{':
            self.gen.push_block()
            self.accept('{')
            self.local_declarations()
            self.statement_list()
            if self.current_token.type == '}':
                self.accept('}')
                self.gen.pop_block()
            else:
                self.result = False
        else:
            self.result = False

    def declaration_prime(self, type_spec, dec_id):
        if self.current_token.type in self.var_declaration_first:
            self.var_declaration(type_spec, dec_id)
        elif self.current_token.type == '(':
            self.accept('(')
            params = self.params()
            self.gen.add_code(['func', dec_id, type_spec, str(len(params))])
            if len(params) > 0:
                for param in params:
                    self.gen.add_code(['param', '\t', '\t', param])
                    self.gen.add_code(['alloc', '4', '\t', param])
            if self.current_token.type == ')':
                self.accept(')')
                self.compound_stmt()
                self.gen.add_code(['end', 'func', dec_id, '\t'])

    def param_prime(self):
        if self.current_token.type == '[':
            self.accept('[')
            if self.current_token.type == ']':
                self.accept(']')
            else:
                self.result = False

    def param(self):
        self.type_specifier()
        if self.current_token.type == 'ID':
            param_id = self.current_token.value
            self.accept('ID')
            self.param_prime()
            return param_id

    def param_list_prime(self):
        if self.current_token.type == ',':
            self.accept(',')
            return self.param_list()
        return []

    def param_list(self):
        params = []
        param_id = self.param()
        params.append(param_id)
        params = params + self.param_list_prime()
        return params

    def params(self):
        params = []
        if self.current_token.type == 'void':
            self.accept('void')
            self.params_prime()
            return params
        elif self.current_token.type == 'int':
            self.accept('int')
            if self.current_token.type == 'ID':
                params.append(self.current_token.value)
                self.accept('ID')
                self.param_prime()
                params = params + self.param_list_prime()
                return params
        else:
            self.result = False

    def params_prime(self):
        if self.current_token.type == 'ID':
            self.accept('ID')
            self.param_prime()
            self.param_list_prime()

    def statement(self):
        if self.current_token.type in self.expression_stmt_first:
            self.expression_stmt()
        elif self.current_token.type in self.compound_stmt_first:
            self.compound_stmt()
        elif self.current_token.type == 'if':
            self.selection_stmt()
        elif self.current_token.type == 'while':
            self.iteration_stmt()
        elif self.current_token.type == 'return':
            self.return_stmt()
        else:
            self.result = False

    def selection_stmt(self):
        if self.current_token.type == 'if':
            self.accept('if')
            if self.current_token.type == '(':
                self.accept('(')
                exp = self.expression()
                if self.current_token.type == ')':
                    self.accept(')')
                    self.gen.add_code(['BRLE', exp, '\t', '???', 'bpe =' + str(self.gen.bpe_push())])
                    self.statement()
                    self.selection_stmt_prime()
                    self.gen.back_patch_e()
                else:
                    self.result = False
            else:
                self.result = False

    def selection_stmt_prime(self):
        if self.current_token.type == 'else':
            self.accept('else')
            self.gen.add_code(['BR', '\t', '\t', '???', 'bpo =' + str(self.gen.bpo_push())])
            self.gen.back_patch_e()
            self.gen.bpe_flag = True
            self.statement()
            self.gen.back_patch_o()

    def iteration_stmt(self):
        if self.current_token.type == 'while':
            self.accept('while')
            if self.current_token.type == '(':
                self.accept('(')
                self.gen.bpw_push()
                exp = self.expression()
                self.gen.add_code(['BRLEQ', exp, '\t', '???', 'bpo= ' + str(self.gen.bpo_push())])
                if self.current_token.type == ')':
                    self.accept(')')
                    self.statement()
                    n = self.gen.bpw_pop()
                    self.gen.add_code(['BR', '\t', '\t', str(n), 'val of bpw'])
                    self.gen.back_patch_o()
                else:
                    self.result = False
            else:
                self.result = False

    def return_stmt(self):
        if self.current_token.type == 'return':
            self.accept('return')
            self.return_stmt_prime()

    def return_stmt_prime(self):
        if self.current_token.type == ';':
            self.accept(';')
        elif self.current_token.type in self.expression_first:
            exp = self.expression()
            self.gen.add_code(['return', '\t', '\t', exp])
            if self.current_token.type == ';':
                self.accept(';')
            else:
                self.result = False
        else:
            self.result = False

    def expression_stmt(self):
        if self.current_token.type in self.expression_first:
            self.expression()
            if self.current_token.type == ';':
                self.accept(';')
            else:
                self.result = False
        elif self.current_token.type == ';':
            self.accept(';')
        else:
            self.result = False

    def expression(self):
        if self.current_token.type == '(':
            self.accept('(')
            exp = self.expression()
            if self.current_token.type == ')':
                self.accept(')')
                val = self.term_prime(exp)
                val = self.additive_expression_prime(val)
                val = self.simple_expression(val)
                return val
            else:
                self.result = False
        elif self.current_token.type == 'ID':
            var_id = self.current_token.value
            self.accept('ID')
            temp = self.expression_prime(var_id)
            return temp
        elif self.current_token.type == 'NUM':
            number = str(self.current_token.value)
            self.accept('NUM')
            val = self.term_prime(number)
            val = self.additive_expression_prime(val)
            val = self.simple_expression(val)
            return val
        else:
            self.result = False

    def expression_prime(self, ref_id):
        if self.current_token.type == '[':
            self.accept(self.current_token)
            exp = self.expression()
            if self.current_token.type == ']':
                self.accept(']')
                temp = self.gen.temp()
                if re.match(r'[0-9]', exp):
                    temp = self.gen.temp()
                    num = int(exp)
                    self.gen.add_code(['disp', ref_id, str(4*num), temp])
                else:
                    self.gen.add_code(['mult', exp, '4', temp])
                    temp2 = self.gen.temp()
                    self.gen.add_code(['disp', ref_id, temp, temp2])
                    temp = temp2
                val = self.expression_double_prime(temp)
                return val
            else:
                self.result = False
        elif self.current_token.type == '(':
            self.accept('(')
            args = self.args()
            if len(args) > 0:
                for arg in args:
                    self.gen.add_code(['arg', '\t', '\t', arg])
            temp = self.gen.temp()
            self.gen.add_code(['call', ref_id, str(len(args)), temp])
            if self.current_token.type == ')':
                self.accept(')')
                val = self.term_prime(temp)
                val = self.additive_expression_prime(val)
                val = self.simple_expression(val)
                return val
            else:
                self.result = False
        else:
            return self.expression_double_prime(ref_id)

    def expression_double_prime(self, ref_id):
        if self.current_token.type == '=':
            self.accept(self.current_token)
            temp = self.expression()
            self.gen.add_code(['assgn', temp, '\t', ref_id])
        else:
            val = self.term_prime(ref_id)
            val = self.additive_expression_prime(val)
            val = self.simple_expression(val)
            return val

    def simple_expression(self, var):
        if self.current_token.type in ['<=', '<', '>', '>=', '==', '!=']:
            self.accept(self.current_token)
            val = self.additive_expression()
            temp = self.gen.temp()
            self.gen.add_code(['compr', var, val, temp])
            return temp
        return var

    def relop(self):
        r = ['<=', '<', '>', '>=', '==', '!=']
        if self.current_token.type in r:
            self.accept(self.current_token.type)
        else:
            self.result = False

    def additive_expression(self):
        val = self.term()
        val = self.additive_expression_prime(val)
        return val

    def additive_expression_prime(self, ref_id):
        if self.current_token.type in ['+', '-']:
            op = self.current_token.value
            self.accept(self.current_token)
            val = self.term()
            val = self.additive_expression_prime(val)
            temp = self.gen.temp()
            if op == '+':
                self.gen.add_code(['add', ref_id+' ', val+' ', temp])
            elif op == '-':
                self.gen.add_code(['sub', ref_id+' ', val+' ', temp])
            return temp
        return ref_id

    def term(self):
        val = self.factor()
        val = self.term_prime(val)
        return val

    def term_prime(self, ref_id):
        if self.current_token.type in ['*', '/']:
            op = self.current_token.value
            self.accept(self.current_token.type)
            fact = self.factor()
            temp = self.gen.temp()
            if op == '*':
                self.gen.add_code(['mult', ref_id, fact, temp])
            else:
                self.gen.add_code(['div', ref_id, fact, temp])
            term = self.term_prime(temp)
            if term is None:
                return temp
            else:
                return term
        return ref_id

    def factor(self):
        if self.current_token.type == '(':
            self.accept(self.current_token)
            exp = self.expression()
            if self.current_token.type == ')':
                self.accept(self.current_token)
                return exp
            else:
                self.result = False
        elif self.current_token.type == 'ID':
            ref_id = self.current_token.value
            self.accept(self.current_token)
            val = self.factor_prime(ref_id)
            return val
        elif self.current_token.type == 'NUM':
            number = str(self.current_token.value)
            self.accept(self.current_token)
            return number
        else:
            self.result = False

    def factor_prime(self, ref_id):
        if self.current_token.type == '[':
            self.accept(self.current_token)
            exp = self.expression()
            if self.current_token.type == ']':
                self.accept(self.current_token)
                temp = self.gen.temp()
                if re.match(r'[0-9]', exp):
                    temp = self.gen.temp()
                    num = int(exp)
                    self.gen.add_code(['disp', ref_id, str(4 * num), temp])
                    return temp
                else:
                    self.gen.add_code(['mult', exp, '4 ', temp])
                    temp2 = self.gen.temp()
                    self.gen.add_code(['disp', ref_id, temp, temp2])
                    temp = temp2
                    return temp
            else:
                self.result = False
        elif self.current_token.type == '(':
            self.accept(self.current_token)
            args = self.args()
            if len(args) > 0:
                for arg in args:
                    self.gen.add_code(['arg', '\t', '\t', arg])
            temp = self.gen.temp()
            self.gen.add_code(['call', ref_id, str(len(args)), temp])
            if self.current_token.type == ')':
                self.accept(self.current_token)
                return temp
            else:
                self.result = False
        return ref_id

    def args(self):
        args = []
        if self.current_token.type in self.expression_first:
            exp = self.expression()
            args.append(exp)
            args = args + self.arg_list()
            return args

    def arg_list(self):
        args = []
        if self.current_token.type == ',':
            self.accept(self.current_token)
            exp = self.expression()
            args.append(exp)
            args = args + self.arg_list()
            return args
        return []


try:
    f = open('input.txt', 'r')
    # file = sys.argv[1]
    # f = open(file, 'r')
    scanner = Scanner(f)
    scanner.run_scanner()
    parse = Parser(scanner.tokens)
    parse.program()

    if parse.result == True:
        sys.stdout.write('\nACCEPT')
    else:
        sys.stdout.write('REJECT')
    f.close()
except IOError:
    print('File not accessible')
