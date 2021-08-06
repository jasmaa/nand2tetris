from typing import TextIO
from tokenizer import Keyword, TokenType, Tokenizer


class CompilerException(Exception):
    pass


class Compiler:
    """Compiles Jack code to XML.
    """

    def __init__(self, in_f: TextIO, out_f: TextIO):
        self.__out_f = out_f
        self.__tokenizer = Tokenizer(in_f)
        self.__tokenizer.advance()

    def compile_class(self):
        """Compiles class.
        """

        if not (self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword == Keyword.CLASS):
            raise CompilerException('Expected keyword `class`.')
        self.__out_f.write('<class>\n')
        self.__out_f.write(f'<keyword> class </keyword>\n')
        self.__tokenizer.advance()

        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected an identifier.')
        class_name = self.__tokenizer.identifier
        self.__out_f.write(f'<identifier> {class_name} </identifier>\n')
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
        self.__out_f.write('<symbol> { </symbol>\n')
        self.__tokenizer.advance()

        # Parse class var declarations
        while self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.STATIC, Keyword.FIELD]:
            self.compile_class_var_dec()

        # Parse subroutine declarations
        while self.__tokenizer.keyword in [Keyword.CONSTRUCTOR, Keyword.FUNCTION, Keyword.METHOD]:
            self.compile_subroutine()

        # End of class body
        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
            raise CompilerException('Expected `}`')
        self.__out_f.write('<symbol> } </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</class>\n')

    def compile_class_var_dec(self):
        """Compiles class variables declaration.
        """

        self.__out_f.write('<classVarDec>\n')

        # Parse static/field class
        var_class = self.__tokenizer.keyword
        self.__out_f.write(f'<keyword> {var_class} </keyword>\n')
        self.__tokenizer.advance()

        # Parse type
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN]:
            var_type = self.__tokenizer.keyword
            self.__out_f.write(f'<keyword> {var_type} </keyword>\n')
        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            var_type = self.__tokenizer.identifier
            self.__out_f.write(f'<identifier> {var_type} </identifier>\n')
        else:
            raise CompilerException('Expected valid type.')
        self.__tokenizer.advance()

        # Parse first variable
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        var_name = self.__tokenizer.identifier
        self.__out_f.write(f'<identifier> {var_name} </identifier>\n')
        self.__tokenizer.advance()

        # Parse additional variables
        while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
            self.__out_f.write('<symbol> , </symbol>\n')
            self.__tokenizer.advance()
            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            var_name = self.__tokenizer.identifier
            self.__out_f.write(f'<identifier> {var_name} </identifier>\n')
            self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__out_f.write('<symbol> ; </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</classVarDec>\n')

    def compile_subroutine(self):
        """Compiles subroutine.
        """

        self.__out_f.write('<subroutineDec>\n')

        # Parse static/field class
        subroutine_class = self.__tokenizer.keyword
        self.__out_f.write(f'<keyword> {subroutine_class} </keyword>\n')
        self.__tokenizer.advance()

        # Parse type
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID]:
            return_type = self.__tokenizer.keyword
            self.__out_f.write(f'<keyword> {return_type} </keyword>\n')
        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            var_type = self.__tokenizer.identifier
            self.__out_f.write(f'<identifier> {var_type} </identifier>\n')
        else:
            raise CompilerException('Expected valid type or void.')
        self.__tokenizer.advance()

        # Parse name
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        subroutine_name = self.__tokenizer.identifier
        self.__out_f.write(f'<identifier> {subroutine_name} </identifier>\n')
        self.__tokenizer.advance()

        # Parse parameter list
        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
            raise CompilerException('Expected symbol `(`.')
        self.__out_f.write('<symbol> ( </symbol>\n')
        self.__tokenizer.advance()

        self.compile_parameter_list()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
            raise CompilerException('Expected symbol `)`.')
        self.__out_f.write('<symbol> ) </symbol>\n')
        self.__tokenizer.advance()

        # Parse subroutine body
        self.__out_f.write('<subroutineBody>\n')

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
        self.__out_f.write('<symbol> { </symbol>\n')
        self.__tokenizer.advance()

        # Parse variable declaration if it exists
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword == Keyword.VAR:
            self.compile_var_dec()
            self.__tokenizer.advance()

        # Parse statement
        # TODO: do this

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
            raise CompilerException('Expected symbol `}`.')
        self.__out_f.write('<symbol> } </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</subroutineBody>\n')
        self.__out_f.write('</subroutineDec>\n')

    def compile_parameter_list(self):
        """Compiles parameter list.
        """

        self.__out_f.write('<parameterList>\n')

        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID] \
                or self.__tokenizer.token_type == TokenType.IDENTIFIER:

            # Parse param type
            if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID]:
                var_type = self.__tokenizer.keyword
                self.__out_f.write(f'<keyword> {var_type} </keyword>\n')
            elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
                var_type = self.__tokenizer.identifier
                self.__out_f.write(f'<identifier> {var_type} </identifier>\n')
            self.__tokenizer.advance()
            # Parse param name
            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            var_name = self.__tokenizer.identifier
            self.__out_f.write(f'<identifier> {var_name} </identifier>\n')
            self.__tokenizer.advance()

            # Parse additional params
            while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
                self.__out_f.write('<symbol> , </symbol>\n')
                self.__tokenizer.advance()
                if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID]:
                    var_type = self.__tokenizer.keyword
                    self.__out_f.write(f'<keyword> {var_type} </keyword>\n')
                elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
                    var_type = self.__tokenizer.identifier
                    self.__out_f.write(
                        f'<identifier> {var_type} </identifier>\n'
                    )
                self.__tokenizer.advance()
                # Parse param name
                if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                    raise CompilerException('Expected valid identifier.')
                var_name = self.__tokenizer.identifier
                self.__out_f.write(f'<identifier> {var_name} </identifier>\n')
                self.__tokenizer.advance()

        self.__out_f.write('</parameterList>\n')

    def compile_var_dec(self):
        """Compiles variable declaration.
        """

        self.__out_f.write('<varDec>\n')
        self.__out_f.write('<keyword> var </keyword>\n')
        self.__tokenizer.advance()

        # Parse type
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN]:
            return_type = self.__tokenizer.keyword
            self.__out_f.write(f'<keyword> {return_type} </keyword>\n')
        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            return_type = self.__tokenizer.identifier
            self.__out_f.write(f'<identifier> {return_type} </identifier>\n')
        else:
            raise CompilerException('Expected valid type.')
        self.__tokenizer.advance()

        # Parse first variable
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        var_name = self.__tokenizer.identifier
        self.__out_f.write(f'<identifier> {var_name} </identifier>\n')
        self.__tokenizer.advance()

        # Parse additional variables
        while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
            self.__out_f.write('<symbol> , </symbol>\n')
            self.__tokenizer.advance()
            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            var_name = self.__tokenizer.identifier
            self.__out_f.write(f'<identifier> {var_name} </identifier>\n')
            self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__out_f.write('<symbol> ; </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</varDec>\n')


if __name__ == '__main__':
    with open('test.jack', 'r') as in_f:
        with open('out.vm', 'w') as out_f:
            c = Compiler(in_f=in_f, out_f=out_f)
            c.compile_class()
