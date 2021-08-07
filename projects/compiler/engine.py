from typing import TextIO
from tokenizer import Keyword, TokenType, Tokenizer


class CompilerException(Exception):
    pass


class CompilationEngine:
    """Compilation engine that compiles Jack code to XML.
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
        while self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword == Keyword.VAR:
            self.compile_var_dec()

        # Parse statements
        self.compile_statements()

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

    def compile_statements(self):
        """Compiles statements.
        """
        self.__out_f.write('<statements>\n')

        while self.__tokenizer.token_type == TokenType.KEYWORD and (
                self.__tokenizer.keyword == Keyword.LET or
                self.__tokenizer.keyword == Keyword.IF or
                self.__tokenizer.keyword == Keyword.DO or
                self.__tokenizer.keyword == Keyword.WHILE or
                self.__tokenizer.keyword == Keyword.RETURN):

            if self.__tokenizer.keyword == Keyword.LET:
                self.compile_let()
            elif self.__tokenizer.keyword == Keyword.IF:
                self.compile_if()
            elif self.__tokenizer.keyword == Keyword.DO:
                self.compile_do()
            elif self.__tokenizer.keyword == Keyword.WHILE:
                self.compile_while()
            elif self.__tokenizer.keyword == Keyword.RETURN:
                self.compile_return()

        self.__out_f.write('</statements>\n')

    def compile_let(self):
        """Compiles let statement.
        """
        self.__out_f.write('<letStatement>\n')
        self.__out_f.write('<keyword> let </keyword>\n')
        self.__tokenizer.advance()

        # Parse name
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        subroutine_name = self.__tokenizer.identifier
        self.__out_f.write(f'<identifier> {subroutine_name} </identifier>\n')
        self.__tokenizer.advance()

        # Parse indexing if possible
        if self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '[':
            self.__out_f.write('<symbol> [ </symbol>\n')
            self.__tokenizer.advance()

            self.compile_expression()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ']'):
                raise CompilerException('Expected symbol `]`.')
            self.__out_f.write('<symbol> ] </symbol>\n')
            self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '='):
            raise CompilerException('Expected symbol `=`.')
        self.__out_f.write('<symbol> = </symbol>\n')
        self.__tokenizer.advance()

        # Parse let body
        self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__out_f.write('<symbol> ; </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</letStatement>\n')

    def compile_if(self):
        """Compiles if statement.
        """
        self.__out_f.write('<ifStatement>\n')
        self.__out_f.write('<keyword> if </keyword>\n')
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
            raise CompilerException('Expected symbol `(`.')
        self.__out_f.write('<symbol> ( </symbol>\n')
        self.__tokenizer.advance()

        # Parse conditional
        self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
            raise CompilerException('Expected symbol `)`.')
        self.__out_f.write('<symbol> ) </symbol>\n')
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
        self.__out_f.write('<symbol> { </symbol>\n')
        self.__tokenizer.advance()

        # Parse if body
        self.compile_statements()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
            raise CompilerException('Expected symbol `}`.')
        self.__out_f.write('<symbol> } </symbol>\n')
        self.__tokenizer.advance()

        # Parse else if exists
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword == Keyword.ELSE:
            self.__out_f.write('<keyword> else </keyword>\n')
            self.__tokenizer.advance()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
                raise CompilerException('Expected symbol `{`.')
            self.__out_f.write('<symbol> { </symbol>\n')
            self.__tokenizer.advance()

            # Parse else body
            self.compile_statements()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
                raise CompilerException('Expected symbol `}`.')
            self.__out_f.write('<symbol> } </symbol>\n')
            self.__tokenizer.advance()

        self.__out_f.write('</ifStatement>\n')

    def compile_while(self):
        """Compiles while statement.
        """
        self.__out_f.write('<whileStatement>\n')
        self.__out_f.write('<keyword> while </keyword>\n')
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
            raise CompilerException('Expected symbol `(`.')
        self.__out_f.write('<symbol> ( </symbol>\n')
        self.__tokenizer.advance()

        # Parse conditional
        self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
            raise CompilerException('Expected symbol `)`.')
        self.__out_f.write('<symbol> ) </symbol>\n')
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
        self.__out_f.write('<symbol> { </symbol>\n')
        self.__tokenizer.advance()

        # Parse loop body
        self.compile_statements()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
            raise CompilerException('Expected symbol `}`.')
        self.__out_f.write('<symbol> } </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</whileStatement>\n')

    def compile_do(self):
        """Compiles do statement.
        """
        self.__out_f.write('<doStatement>\n')
        self.__out_f.write('<keyword> do </keyword>\n')
        self.__tokenizer.advance()

        # Parse subroutine call
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier')

        id_name = self.__tokenizer.identifier
        self.__out_f.write(f'<identifier> {id_name} </identifier>\n')
        self.__tokenizer.advance()

        if self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(':
            # Local call
            self.__out_f.write('<symbol> ( </symbol>\n')
            self.__tokenizer.advance()

            self.compile_expression_list()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                raise CompilerException('Expected symbol `)`.')
            self.__out_f.write('<symbol> ) </symbol>\n')
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '.':
            # External call
            self.__out_f.write('<symbol> . </symbol>\n')
            self.__tokenizer.advance()

            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            subroutine_name = self.__tokenizer.identifier
            self.__out_f.write(
                f'<identifier> {subroutine_name} </identifier>\n')
            self.__tokenizer.advance()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
                raise CompilerException('Expected symbol `(`.')
            self.__out_f.write('<symbol> ( </symbol>\n')
            self.__tokenizer.advance()

            self.compile_expression_list()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                raise CompilerException('Expected symbol `)`.')
            self.__out_f.write('<symbol> ) </symbol>\n')
            self.__tokenizer.advance()
        else:
            raise CompilerException('Expected either symbol `(` or `.`.')

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__out_f.write('<symbol> ; </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</doStatement>\n')

    def compile_return(self):
        """Compile return statement.
        """
        self.__out_f.write('<returnStatement>\n')
        self.__out_f.write('<keyword> return </keyword>\n')
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            # Parse expression
            self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__out_f.write('<symbol> ; </symbol>\n')
        self.__tokenizer.advance()

        self.__out_f.write('</returnStatement>\n')

    def compile_expression(self):
        """Compiles expression.
        """
        self.__out_f.write('<expression>\n')

        self.compile_term()

        # Compile additional arguments if exist
        while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol in '+-*/&|<>=':
            op = self.__tokenizer.symbol
            # Replace with alt code
            if op == '<':
                op = '&lt;'
            elif op == '>':
                op = '&gt;'
            elif op == '&':
                op = '&amp;'
            self.__out_f.write(
                f'<symbol> {op} </symbol>\n'
            )
            self.__tokenizer.advance()

            self.compile_term()

        self.__out_f.write('</expression>\n')

    def compile_term(self):
        """Compiles term.
        """
        self.__out_f.write('<term>\n')

        if self.__tokenizer.token_type == TokenType.INT_CONST:
            # Integer constant
            self.__out_f.write(
                f'<integerConstant> {self.__tokenizer.int_val} </integerConstant>\n'
            )
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.STRING_CONST:
            # String constant
            self.__out_f.write(
                f'<stringConstant> {self.__tokenizer.string_val} </stringConstant>\n'
            )
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.TRUE, Keyword.FALSE, Keyword.NULL, Keyword.THIS]:
            # Keyword constant
            self.__out_f.write(
                f'<keyword> {self.__tokenizer.keyword} </keyword>\n'
            )
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            id_name = self.__tokenizer.identifier
            self.__out_f.write(f'<identifier> {id_name} </identifier>\n')
            self.__tokenizer.advance()

            if self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '[':
                # Array indexing
                self.__out_f.write('<symbol> [ </symbol>\n')
                self.__tokenizer.advance()

                self.compile_expression()

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ']'):
                    raise CompilerException('Expected symbol `]`.')
                self.__out_f.write('<symbol> ] </symbol>\n')
                self.__tokenizer.advance()

            elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(':
                # Subroutine local call
                self.__out_f.write('<symbol> ( </symbol>\n')
                self.__tokenizer.advance()

                self.compile_expression_list()

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                    raise CompilerException('Expected symbol `)`.')
                self.__out_f.write('<symbol> ) </symbol>\n')
                self.__tokenizer.advance()

            elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '.':
                # Subroutine external call
                self.__out_f.write('<symbol> . </symbol>\n')
                self.__tokenizer.advance()

                if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                    raise CompilerException('Expected valid identifier.')
                subroutine_name = self.__tokenizer.identifier
                self.__out_f.write(
                    f'<identifier> {subroutine_name} </identifier>\n')
                self.__tokenizer.advance()

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
                    raise CompilerException('Expected symbol `(`.')
                self.__out_f.write('<symbol> ( </symbol>\n')
                self.__tokenizer.advance()

                self.compile_expression_list()

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                    raise CompilerException('Expected symbol `)`.')
                self.__out_f.write('<symbol> ) </symbol>\n')
                self.__tokenizer.advance()

            else:
                # Variable access
                pass

        elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(':
            # Parenthesis-wrapped expression
            self.__out_f.write('<symbol> ( </symbol>\n')
            self.__tokenizer.advance()

            self.compile_expression()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                raise CompilerException('Expected symbol `)`.')
            self.__out_f.write('<symbol> ) </symbol>\n')
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol in '-~':
            # Unary operation
            self.__out_f.write(
                f'<symbol> {self.__tokenizer.symbol} </symbol>\n'
            )
            self.__tokenizer.advance()

            self.compile_term()

        self.__out_f.write('</term>\n')

    def compile_expression_list(self):
        """Compiles expression list.
        """
        self.__out_f.write('<expressionList>\n')

        # Parse expression list if exists
        if self.__tokenizer.token_type == TokenType.INT_CONST or \
                self.__tokenizer.token_type == TokenType.STRING_CONST or \
                self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.TRUE, Keyword.FALSE, Keyword.NULL, Keyword.THIS] or \
                self.__tokenizer.token_type == TokenType.IDENTIFIER or \
                self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(' or \
                self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol in '-~':

            # Parse first expression
            self.compile_expression()

            # Parse additional expressions
            while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
                self.__out_f.write('<symbol> , </symbol>\n')
                self.__tokenizer.advance()

                self.compile_expression()

        self.__out_f.write('</expressionList>\n')
