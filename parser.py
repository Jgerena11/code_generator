from scanner import *
import sys


class Parser:

    class CodeGen:
        count = 0
        temp_var = 0
        bp = []
        code = {}

        def add_code(self, quad):
            self.code.update({str(self.count): quad})

        # def print_quadruple(self, *quad):
        #     print(str(self.count), end="\t")
        #     for string in quad:
        #         string = string + '  '
        #         print(string, end="\t")
        #     print('\n', end='')
        #     self.count += 1

        def print_quadruples(self):
            for i in range(1, self.count+1):
                print(str(i), end="\t")
                for string in self.code[str(i)]:
                    string = string + ' '
                    print(string, end="\t")
                print('\n', end='')
                self.count += 1

        def temp(self):
            t = self.temp_var
            self.temp_var += 1
            return str('_t'+str(t))

        def back_patch(self, string):
            return string

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
            self.gen.print_quadruple('alloc', '4 ', '----', dec_id)
            return
        elif self.current_token.type == '[':
            self.accept('[')
            if self.current_token.type == 'NUM':
                number = int(self.current_token.value)
                self.accept('NUM')
                self.gen.print_quadruple('alloc', str(4 * number), '\t', dec_id)
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
            self.accept('{')
            self.local_declarations()
            self.statement_list()
            if self.current_token.type == '}':
                self.accept('}')
            else:
                self.result = False
        else:
            self.result = False

    def declaration_prime(self, type_spec, dec_id):
        if self.current_token.type in self.var_declaration_first:
            self.var_declaration()
        elif self.current_token.type == '(':
            self.accept('(')
            params = self.params()
            self.gen.print_quadruple('func', dec_id, type_spec, str(len(params)))
            if len(params) > 0:
                for param in params:
                    self.gen.print_quadruple('param', '----', '----', param)
            if self.current_token.type == ')':
                self.accept(')')
                self.compound_stmt()

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
                    self.gen.print_quadruple('BR', exp, '\t',  )
                    self.statement()
                    self.selection_stmt_prime()
                else:
                    self.result = False
            else:
                self.result = False

    def selection_stmt_prime(self):
        if self.current_token.type == 'else':
            self.accept('else')
            self.statement()

    def iteration_stmt(self):
        if self.current_token.type == 'while':
            self.accept('while')
            if self.current_token.type == '(':
                self.accept('(')
                self.expression()
                if self.current_token.type == ')':
                    self.accept(')')
                    self.statement()
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
            self.expression()
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
            exp = int(self.expression())
            if self.current_token.type == ']':
                self.accept(']')
                temp = self.gen.temp()
                self.gen.print_quadruple('disp', ref_id, str(4*exp), temp)
                val = self.expression_double_prime(temp)
                return val
            else:
                self.result = False
        elif self.current_token.type == '(':
            self.accept('(')
            self.args()
            if self.current_token.type == ')':
                self.accept(')')
                self.term_prime()
                self.additive_expression_prime(ref_id)
                self.simple_expression()
            else:
                self.result = False
        elif self.current_token.type in self.expression_double_prime_first:
            return self.expression_double_prime(ref_id)

    def expression_double_prime(self, ref_id):
        if self.current_token.type == '=':
            self.accept(self.current_token)
            temp = self.expression()
            self.gen.print_quadruple('assgn', temp, '\t', ref_id)
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
            self.gen.print_quadruple('compr', var, val, temp)
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
                self.gen.print_quadruple('add', ref_id+' ', val+' ', temp)
            else:
                self.gen.print_quadruple('sub', ref_id+' ', val+' ', temp)
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
                self.gen.print_quadruple('mult', ref_id+' ', fact+' ', temp)
            else:
                self.gen.print_quadruple('div', ref_id+' ', fact+' ', temp)
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
            self.factor_prime()
            return ref_id
        elif self.current_token.type == 'NUM':
            number = str(self.current_token.value)
            self.accept(self.current_token)
            return number
        else:
            self.result = False

    def factor_prime(self):
        if self.current_token.type == '[':
            self.accept(self.current_token)
            self.expression()
            if self.current_token.type == ']':
                self.accept(self.current_token)
            else:
                self.result = False
        elif self.current_token.type == '(':
            self.accept(self.current_token)
            self.args()
            if self.current_token.type == ')':
                self.accept(self.current_token)
            else:
                self.result = False

    def args(self):
        if self.current_token.type in self.expression_first:
            self.expression()
            self.arg_list()

    def arg_list(self):
        if self.current_token.type == ',':
            self.accept(self.current_token)
            self.expression()
            self.arg_list()


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
