from symbol_table import IdentifierKind, SymbolTable
from typing import TextIO
from tokenizer import Keyword, TokenType, Tokenizer
from writer import Command, Segment, VMWriter


class CompilerException(Exception):
    pass


kind2seg = {
    IdentifierKind.STATIC: Segment.STATIC,
    IdentifierKind.FIELD: Segment.THIS,
    IdentifierKind.ARGUMENT: Segment.ARG,
    IdentifierKind.VAR: Segment.LOCAL,
}


class CompilationEngine:
    """Compilation engine that compiles Jack code to VM code.
    """

    def __init__(self, in_f: TextIO, out_f: TextIO):
        self.__out_f = out_f
        self.__writer = VMWriter(out_f)
        self.__symbol_table = SymbolTable()
        self.__class_name = None
        self.__return_type = None
        self.__labels = {}
        self.__tokenizer = Tokenizer(in_f)
        self.__tokenizer.advance()

    def compile_class(self):
        """Compiles class.
        """
        if not (self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword == Keyword.CLASS):
            raise CompilerException('Expected keyword `class`.')
        self.__tokenizer.advance()

        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected an identifier.')
        self.__class_name = self.__tokenizer.identifier
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
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
        self.__tokenizer.advance()

    def compile_class_var_dec(self):
        """Compiles class variables declaration.
        """
        # Parse static/field kind
        var_kind = self.__tokenizer.keyword
        self.__tokenizer.advance()

        # Parse type
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN]:
            var_type = self.__tokenizer.keyword
        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            var_type = self.__tokenizer.identifier
        else:
            raise CompilerException('Expected valid type.')
        self.__tokenizer.advance()

        # Parse first variable
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        var_name = self.__tokenizer.identifier
        self.__tokenizer.advance()

        self.__symbol_table.define(var_name, var_type, var_kind)

        # Parse additional variables
        while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
            self.__tokenizer.advance()

            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            var_name = self.__tokenizer.identifier
            self.__tokenizer.advance()

            self.__symbol_table.define(var_name, var_type, var_kind)

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__tokenizer.advance()

    def compile_subroutine(self):
        """Compiles subroutine declaration.
        """
        # Reset symbol table
        self.__symbol_table.start_subroutine()

        # Parse constructor/function/method kind
        subroutine_kind = self.__tokenizer.keyword

        self.__tokenizer.advance()

        # Parse return type
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID]:
            self.__return_type = self.__tokenizer.keyword
        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            self.__return_type = self.__tokenizer.identifier
        else:
            raise CompilerException('Expected valid type or void.')
        self.__tokenizer.advance()

        # Parse name
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        subroutine_name = f'{self.__class_name}.{self.__tokenizer.identifier}'
        self.__tokenizer.advance()

        # Add dummy self as first parameter if method
        if subroutine_kind == Keyword.METHOD:
            self.__symbol_table.define(
                'this', self.__class_name, IdentifierKind.ARGUMENT)

        # Parse parameter list
        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
            raise CompilerException('Expected symbol `(`.')
        self.__tokenizer.advance()

        self.compile_parameter_list()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
            raise CompilerException('Expected symbol `)`.')
        self.__tokenizer.advance()

        # Parse subroutine body

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
        self.__tokenizer.advance()

        # Parse variable declaration if it exists
        while self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword == Keyword.VAR:
            self.compile_var_dec()

        n_locals = self.__symbol_table.var_count(IdentifierKind.VAR)
        self.__writer.write_function(subroutine_name, n_locals)

        if subroutine_kind == Keyword.CONSTRUCTOR:
            # Allocate memory for object if constructor
            n_fields = self.__symbol_table.var_count(IdentifierKind.FIELD)
            self.__writer.write_push(Segment.CONST, n_fields)
            self.__writer.write_call('Memory.alloc', 1)
            self.__writer.write_pop(Segment.POINTER, 0)

        elif subroutine_kind == Keyword.METHOD:
            # Copy arg0 to pointer0
            self.__writer.write_push(Segment.ARG, 0)
            self.__writer.write_pop(Segment.POINTER, 0)

        # Parse statements
        self.compile_statements()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
            raise CompilerException('Expected symbol `}`.')
        self.__tokenizer.advance()

    def compile_parameter_list(self):
        """Compiles parameter list.
        """
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID] \
                or self.__tokenizer.token_type == TokenType.IDENTIFIER:

            # Parse param type
            if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID]:
                var_type = self.__tokenizer.keyword
            elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
                var_type = self.__tokenizer.identifier
            self.__tokenizer.advance()

            # Parse param name
            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            var_name = self.__tokenizer.identifier
            self.__tokenizer.advance()

            self.__symbol_table.define(
                var_name, var_type, IdentifierKind.ARGUMENT
            )

            # Parse additional params
            while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
                self.__tokenizer.advance()
                if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN, Keyword.VOID]:
                    var_type = self.__tokenizer.keyword
                elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
                    var_type = self.__tokenizer.identifier
                self.__tokenizer.advance()

                # Parse param name
                if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                    raise CompilerException('Expected valid identifier.')
                var_name = self.__tokenizer.identifier
                self.__tokenizer.advance()

                self.__symbol_table.define(
                    var_name, var_type, IdentifierKind.ARGUMENT
                )

    def compile_var_dec(self):
        """Compiles variable declaration.
        """
        self.__tokenizer.advance()

        # Parse type
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.INT, Keyword.CHAR, Keyword.BOOLEAN]:
            var_type = self.__tokenizer.keyword
        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            var_type = self.__tokenizer.identifier
        else:
            raise CompilerException('Expected valid type.')
        self.__tokenizer.advance()

        # Parse first variable
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        var_name = self.__tokenizer.identifier
        self.__tokenizer.advance()

        self.__symbol_table.define(var_name, var_type, IdentifierKind.VAR)

        # Parse additional variables
        while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
            self.__tokenizer.advance()

            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            var_name = self.__tokenizer.identifier
            self.__tokenizer.advance()

            self.__symbol_table.define(var_name, var_type, IdentifierKind.VAR)

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__tokenizer.advance()

    def compile_statements(self):
        """Compiles statements.
        """
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

    def compile_let(self):
        """Compiles let statement.
        """
        self.__tokenizer.advance()

        # Parse name
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier.')
        var_name = self.__tokenizer.identifier
        self.__tokenizer.advance()

        # Parse array indexing if possible
        is_indexing = False
        if self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '[':
            self.__tokenizer.advance()

            self.compile_expression()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ']'):
                raise CompilerException('Expected symbol `]`.')
            self.__tokenizer.advance()

            is_indexing = True

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '='):
            raise CompilerException('Expected symbol `=`.')
        self.__tokenizer.advance()

        # Parse let body
        self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__tokenizer.advance()

        if is_indexing:
            # Indexing, load value into array
            v = self.__symbol_table.find(var_name)
            if v == None:
                raise CompilerException(
                    f'`No declaration for {var_name}` was found.'
                )
            var_type, var_kind, var_idx = v
            self.__writer.write_pop(Segment.TEMP, 0)
            self.__writer.write_push(kind2seg[var_kind], var_idx)
            self.__writer.write_arithmetic(Command.ADD)
            self.__writer.write_pop(Segment.POINTER, 1)
            self.__writer.write_push(Segment.TEMP, 0)
            self.__writer.write_pop(Segment.THAT, 0)

        else:
            # Not indexing, load value into variable
            v = self.__symbol_table.find(var_name)
            if v == None:
                raise CompilerException(
                    f'No declaration found for `{var_name}`.'
                )
            var_type, var_kind, var_idx = v
            self.__writer.write_pop(kind2seg[var_kind], var_idx)

    def compile_if(self):
        """Compiles if statement.
        """
        else_label = self.__generate_label('ELSE')
        endif_label = self.__generate_label('ENDIF')

        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
            raise CompilerException('Expected symbol `(`.')
        self.__tokenizer.advance()

        # Parse conditional
        self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
            raise CompilerException('Expected symbol `)`.')
        self.__tokenizer.advance()

        self.__writer.write_arithmetic(Command.NOT)

        self.__writer.write_if(else_label)

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
        self.__tokenizer.advance()

        # Parse if body
        self.compile_statements()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
            raise CompilerException('Expected symbol `}`.')
        self.__tokenizer.advance()

        self.__writer.write_goto(endif_label)

        self.__writer.write_label(else_label)

        # Parse else if exists
        if self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword == Keyword.ELSE:
            self.__tokenizer.advance()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
                raise CompilerException('Expected symbol `{`.')
            self.__tokenizer.advance()

            # Parse else body
            self.compile_statements()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
                raise CompilerException('Expected symbol `}`.')
            self.__tokenizer.advance()

        self.__writer.write_label(endif_label)

    def compile_while(self):
        """Compiles while statement.
        """
        loop_label = self.__generate_label('LOOP')
        endloop_label = self.__generate_label('ENDLOOP')

        self.__writer.write_label(loop_label)

        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
            raise CompilerException('Expected symbol `(`.')
        self.__tokenizer.advance()

        # Parse conditional
        self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
            raise CompilerException('Expected symbol `)`.')
        self.__tokenizer.advance()

        self.__writer.write_arithmetic(Command.NOT)

        self.__writer.write_if(endloop_label)

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '{'):
            raise CompilerException('Expected symbol `{`.')
        self.__tokenizer.advance()

        # Parse loop body
        self.compile_statements()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '}'):
            raise CompilerException('Expected symbol `}`.')
        self.__tokenizer.advance()

        self.__writer.write_goto(loop_label)

        self.__writer.write_label(endloop_label)

    def compile_do(self):
        """Compiles do statement.
        """
        self.__tokenizer.advance()

        # Parse subroutine call
        if self.__tokenizer.token_type != TokenType.IDENTIFIER:
            raise CompilerException('Expected valid identifier')

        id_name = self.__tokenizer.identifier
        self.__tokenizer.advance()

        if self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(':
            # Internal call
            self.__tokenizer.advance()

            # Guaranteed to be a method. Push address of `this` stack.
            self.__writer.write_push(Segment.POINTER, 0)
            n_args = self.compile_expression_list() + 1

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                raise CompilerException('Expected symbol `)`.')
            self.__tokenizer.advance()

            subroutine_name = f'{self.__class_name}.{id_name}'
            self.__writer.write_call(subroutine_name, n_args)

        elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '.':
            # External call
            self.__tokenizer.advance()

            if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                raise CompilerException('Expected valid identifier.')
            subroutine_name = self.__tokenizer.identifier
            self.__tokenizer.advance()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
                raise CompilerException('Expected symbol `(`.')
            self.__tokenizer.advance()

            # Check subroutine type
            v = self.__symbol_table.find(id_name)
            if v == None:
                # Not in symbol table, class name
                subroutine_name = f'{id_name}.{subroutine_name}'
                n_args = self.compile_expression_list()
            else:
                # Was in symbol table, var name
                var_type, var_kind, var_idx = v
                subroutine_name = f'{var_type}.{subroutine_name}'
                self.__writer.write_push(kind2seg[var_kind], var_idx)
                n_args = self.compile_expression_list() + 1

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                raise CompilerException('Expected symbol `)`.')
            self.__tokenizer.advance()

            self.__writer.write_call(subroutine_name, n_args)

        else:
            raise CompilerException('Expected either symbol `(` or `.`.')

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__tokenizer.advance()

        # Ignore returned value
        self.__writer.write_pop(Segment.TEMP, 0)

    def compile_return(self):
        """Compile return statement.
        """
        self.__tokenizer.advance()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            # Parse expression
            self.compile_expression()

        if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ';'):
            raise CompilerException('Expected symbol `;`.')
        self.__tokenizer.advance()

        # Return 0 if void return type
        if self.__return_type == Keyword.VOID:
            self.__writer.write_push(Segment.CONST, 0)

        self.__writer.write_return()

    def compile_expression(self):
        """Compiles expression.
        """
        self.compile_term()

        # Compile additional arguments if exist
        while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol in '+-*/&|<>=':
            op = self.__tokenizer.symbol
            self.__tokenizer.advance()

            self.compile_term()

            if op == '*':
                self.__writer.write_call('Math.multiply', 2)
            elif op == '/':
                self.__writer.write_call('Math.divide', 2)
            else:
                op2cmd = {
                    '+': Command.ADD,
                    '-': Command.SUB,
                    '&': Command.AND,
                    '|': Command.OR,
                    '<': Command.LT,
                    '>': Command.GT,
                    '=': Command.EQ,
                }
                self.__writer.write_arithmetic(op2cmd[op])

    def compile_term(self):
        """Compiles term.
        """
        if self.__tokenizer.token_type == TokenType.INT_CONST:
            # Integer constant
            self.__writer.write_push(Segment.CONST, self.__tokenizer.int_val)
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.STRING_CONST:
            # String constant
            self.__writer.write_push(
                Segment.CONST, len(self.__tokenizer.string_val)
            )
            self.__writer.write_call('String.new', 1)
            for c in self.__tokenizer.string_val:
                self.__writer.write_push(Segment.CONST, ord(c))
                self.__writer.write_call('String.appendChar', 2)
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.TRUE, Keyword.FALSE, Keyword.NULL, Keyword.THIS]:
            # Keyword constant
            if self.__tokenizer.keyword in [Keyword.FALSE, Keyword.NULL]:
                self.__writer.write_push(
                    Segment.CONST, 0
                )
            elif self.__tokenizer.keyword == Keyword.TRUE:
                self.__writer.write_push(
                    Segment.CONST, 0
                )
                self.__writer.write_arithmetic(Command.NOT)
            elif self.__tokenizer.keyword == Keyword.THIS:
                self.__writer.write_push(
                    Segment.POINTER, 0
                )
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.IDENTIFIER:
            id_name = self.__tokenizer.identifier
            self.__tokenizer.advance()

            if self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '[':
                # Array indexing
                self.__tokenizer.advance()

                self.compile_expression()

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ']'):
                    raise CompilerException('Expected symbol `]`.')
                self.__tokenizer.advance()

                # Point to target locatioin and push value
                v = self.__symbol_table.find(id_name)
                if v == None:
                    raise CompilerException(
                        f'`No declaration for {id_name}` was found.'
                    )
                var_type, var_kind, var_idx = v
                self.__writer.write_push(kind2seg[var_kind], var_idx)
                self.__writer.write_arithmetic(Command.ADD)
                self.__writer.write_pop(Segment.POINTER, 1)
                self.__writer.write_push(Segment.THAT, 0)

            elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(':
                # Subroutine internal call
                self.__tokenizer.advance()

                # Guaranteed to be a method. Push address of `this` stack.
                self.__writer.write_push(Segment.POINTER, 0)
                n_args = self.compile_expression_list() + 1

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                    raise CompilerException('Expected symbol `)`.')
                self.__tokenizer.advance()

                subroutine_name = f'{self.__class_name}.{id_name}'
                self.__writer.write_call(subroutine_name, n_args)

            elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '.':
                # Subroutine external call
                self.__tokenizer.advance()

                if self.__tokenizer.token_type != TokenType.IDENTIFIER:
                    raise CompilerException('Expected valid identifier.')
                subroutine_name = self.__tokenizer.identifier
                self.__tokenizer.advance()

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '('):
                    raise CompilerException('Expected symbol `(`.')
                self.__tokenizer.advance()

                # Check subroutine type
                v = self.__symbol_table.find(id_name)
                if v == None:
                    # Not in symbol table, class name
                    subroutine_name = f'{id_name}.{subroutine_name}'
                    n_args = self.compile_expression_list()
                else:
                    # Was in symbol table, var name
                    var_type, var_kind, var_idx = v
                    subroutine_name = f'{var_type}.{subroutine_name}'
                    self.__writer.write_push(kind2seg[var_kind], var_idx)
                    n_args = self.compile_expression_list() + 1

                if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                    raise CompilerException('Expected symbol `)`.')
                self.__tokenizer.advance()

                self.__writer.write_call(subroutine_name, n_args)

            else:
                # Variable access
                var_name = id_name
                v = self.__symbol_table.find(var_name)
                if v == None:
                    raise CompilerException(
                        f'No declaration found for `{var_name}`.')
                var_type, var_kind, var_idx = v
                self.__writer.write_push(kind2seg[var_kind], var_idx)

        elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(':
            # Parenthesis-wrapped expression
            self.__tokenizer.advance()

            self.compile_expression()

            if not (self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ')'):
                raise CompilerException('Expected symbol `)`.')
            self.__tokenizer.advance()

        elif self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol in '-~':
            # Unary operation
            op = self.__tokenizer.symbol
            self.__tokenizer.advance()

            self.compile_term()

            if op == '-':
                self.__writer.write_arithmetic(Command.NEG)
            elif op == '~':
                self.__writer.write_arithmetic(Command.NOT)

    def compile_expression_list(self) -> int:
        """Compiles expression list. Returns number of arguments encountered.
        """
        n_args = 0

        # Parse expression list if exists
        if self.__tokenizer.token_type == TokenType.INT_CONST or \
                self.__tokenizer.token_type == TokenType.STRING_CONST or \
                self.__tokenizer.token_type == TokenType.KEYWORD and self.__tokenizer.keyword in [Keyword.TRUE, Keyword.FALSE, Keyword.NULL, Keyword.THIS] or \
                self.__tokenizer.token_type == TokenType.IDENTIFIER or \
                self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == '(' or \
                self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol in '-~':

            # Parse first expression
            self.compile_expression()
            n_args += 1

            # Parse additional expressions
            while self.__tokenizer.token_type == TokenType.SYMBOL and self.__tokenizer.symbol == ',':
                self.__tokenizer.advance()

                self.compile_expression()
                n_args += 1

        return n_args

    def __generate_label(self, prefix: str = 'LBL') -> str:
        if prefix in self.__labels:
            self.__labels[prefix] += 1
        else:
            self.__labels[prefix] = 0
        return f'{prefix}_{self.__labels[prefix]}'
