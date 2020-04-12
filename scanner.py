import re

class Token:
    def __init__(self, type, value):
        self.value = value
        self.type = type

class Scanner:
    # --------compiled patterns---------
    open_comment = re.compile(r'/\*|//')
    close_comment = re.compile(r'\*/')
    special_sym = re.compile(r'\+|-|\*|/|<|>|;|,|\(|\)|\[|]|\{|}|=')
    compound_special_symbols = re.compile(r'>=|<=|!=|==')
    words = re.compile(r'[a-zA-Z]')
    Nums = re.compile(r'[0-9]')
    kw = re.compile(r'\belse\b|\bif\b|\breturn\b|\bvoid\b|\bwhile\b|\bint\b')

    tokens = []

    def __init__(self, f):
        self.f = f
        self.line = self.f.readline()

    def add_token(self, token_type, value):
        token = Token(token_type, value)
        self.tokens.append(token)

    def error(self, text, i):
        error = text[i]
        i+=1
        self.add_token('ERROR', 'ERROR')
        return i

    #process comments
    def comments(self, text, i, symbol):
        self.line = text
        comment = ""
        if symbol == '//':
            self.line = self.f.readline()
            return 0
        else:
            while self.line and not self.line.isspace():
                x = re.search('\*/', self.line)
                if x:
                    return x.end()
                self.line = self.f.readline()

    #process special symbols
    def special_symbols(self, text, i):
        j = i+1
        while i < len(text) and re.match('[^\w\s]', text[i]):
            if j < len(text) and re.match('[^\w\s]', text[j]):
                if self.open_comment.match(text[i:j+1]):
                    return self.comments(text[i+2:len(text)], i, text[i:j+1])
                if self.compound_special_symbols.match(text[i:j+1]):
                    self.add_token(text[i:j+1], text[i:j+1])
                    i += 2
                    j += 1
                elif self.special_sym.match(text[i]):
                    self.add_token(text[i], text[i])
                    i += 1
                    j += 1
                elif not self.special_sym.match(text[i]):
                    return self.error(text, i)
            else:
                if self.special_sym.match(text[i]):
                    self.add_token(text[i], text[i])
                elif not self.special_sym.match(text[i]):
                    return self.error(text, i)
                i += 1
        return i

    #process letters
    def letters(self, text, i):
        word = ""
        while i < len(text) and self.words.match(text[i]):
            word += text[i]
            if text[i] == '_':
                if self.words.match(word):
                    self.add_token('ID', word)
                return self.error(text, i)
            i += 1
        if self.kw.match(word):
            self.add_token(word, word)
            return i
        else:
            self.add_token('ID', word)
        return i

    #process numbers
    def numbers(self, text, i):
        NUM = ""
        while i < len(text) and self.Nums.match(text[i]):
            NUM += text[i]
            i += 1
        self.add_token('NUM', NUM)
        return i

    def run_scanner(self):
        while self.line:
            if self.line.isspace():
                self.line = self.f.readline()
                continue
            i = 0
            while i < len(self.line) and self.line[i] != '\n':
                if re.match('[a-zA-Z_]', self.line[i]):
                    i = self.letters(self.line, i)
                    continue
                elif self.Nums.match(self.line[i]):
                    i = self.numbers(self.line, i)
                    continue
                elif re.match(r'[^\w\s]', self.line[i]):
                    i = self.special_symbols(self.line, i)
                    continue
                else:
                    i += 1
            self.line = self.f.readline()
        self.add_token('$', '$')