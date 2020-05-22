class Parser(private val tokens: List<Token>) {
    private class ParseError : RuntimeException()

    private var current = 0

    fun parse(): List<Stmt> {
        val statements = ArrayList<Stmt>()
        while (this.peek().type != TokenType.EOF) {
            val decl = this.declaration()
            if (decl != null) statements.add(decl)
        }
        return statements
    }

    private fun match(vararg types: TokenType): Boolean {
        for (type in types) {
            if (this.check(type)) {
                this.advance()
                return true
            }
        }
        return false
    }

    private fun advance() {
        if (this.peek().type != TokenType.EOF) {
            this.current++
        }
    }

    private fun peek(): Token {
        return this.tokens[this.current]
    }

    private fun previous(): Token {
        return this.tokens[this.current - 1]
    }

    private fun consume(type: TokenType, message: String): Token {
        if (this.check(type)) {
            this.advance()
            return this.previous()
        }
        throw this.error(this.peek(), message)
    }

    private fun error(token: Token, message: String): ParseError {
        Lox.error(token, message)
        return ParseError()
    }

    private fun check(type: TokenType): Boolean {
        return when (this.peek().type) {
            TokenType.EOF -> false
            type -> true
            else -> false
        }
    }

    private fun declaration(): Stmt? {
        return try {
            if (this.match(TokenType.VAR)) this.varDeclaration()
            else this.statement()
        } catch (error: ParseError) {
            this.synchronize()
            null
        }
    }

    private fun varDeclaration(): Stmt {
        val name = this.consume(TokenType.IDENTIFIER, "Expect variable name")

        val initializer = if (this.match(TokenType.EQUAL)) {
            this.expression()
        } else {
            null
        }

        this.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Stmt.Var(name, initializer)
    }

    private fun statement(): Stmt {
        return when {
            this.match(TokenType.PRINT) -> this.printStatement()
            this.match(TokenType.LEFT_BRACE) -> Stmt.Block(this.block())
            this.match(TokenType.IF) -> this.ifStatement()
            this.match(TokenType.WHILE) -> this.whileStatement()
            else -> this.expressionStatement()
        }
    }

    private fun block(): List<Stmt> {
        val statements = ArrayList<Stmt>()


        while (!this.check(TokenType.RIGHT_BRACE) && this.peek().type != TokenType.EOF) {
            val decl = this.declaration()
            if (decl != null) {
                statements.add(decl)
            }
        }
        this.consume(TokenType.RIGHT_BRACE, "Expect } after block")
        return statements
    }

    private fun printStatement(): Stmt {
        val value = this.expression()
        this.consume(TokenType.SEMICOLON, "Expect ';' after value")
        return Stmt.Print(value)
    }

    private fun ifStatement(): Stmt {
        this.consume(TokenType.LEFT_PAREN, "Expect ( after if")
        val cond = this.expression()
        this.consume(TokenType.RIGHT_PAREN, "Expect ) after if condition")

        val thenBranch = this.statement()
        val elseBranch = if (this.match(TokenType.ELSE)) {
            this.statement()
        } else null

        return Stmt.If(cond, thenBranch, elseBranch)
    }

    private fun whileStatement(): Stmt {
        this.consume(TokenType.LEFT_PAREN, "Expect ( after while")
        val cond = this.expression()
        this.consume(TokenType.RIGHT_PAREN, "Expect ) after while condition")

        return Stmt.While(cond, this.statement())
    }

    private fun expressionStatement(): Stmt {
        val expr = this.expression()
        this.consume(TokenType.SEMICOLON, "Expect ';' after expression")
        return Stmt.Expression(expr)
    }

    private fun expression(): Expr {
        return this.assignment()
    }

    private fun assignment(): Expr {
        val expr = this.or()

        if (this.match(TokenType.EQUAL)) { // Assignment
            val equals = this.previous()
            val value = this.assignment()

            if (expr is Expr.Variable) {
                // rvalue to lvalue
                return Expr.Assign(expr.name, value)
            } else {
                this.error(equals, "Invalid assignment target")
            }
        }
        return expr
    }

    private fun or(): Expr {
        var expr = this.and()
        while (this.match(TokenType.OR)) {
            val op = this.previous()
            val right = this.and()
            expr = Expr.Logical(expr, op, right)
        }
        return expr
    }

    private fun and(): Expr {
        var expr = this.equality()
        while (this.match(TokenType.AND)) {
            val op = this.previous()
            val right = this.equality()
            expr = Expr.Logical(expr, op, right)
        }
        return expr
    }

    private fun equality(): Expr {
        var expr = this.comparison()
        while (this.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL)) {
            val operator = this.previous()
            val right = this.comparison()
            expr = Expr.Binary(expr, operator, right)
        }
        return expr
    }

    private fun comparison(): Expr {
        var expr = this.addition()
        while (this.match(
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL
            )
        ) {
            val operator = this.previous()
            val right = this.addition()
            expr = Expr.Binary(expr, operator, right)
        }
        return expr
    }

    private fun addition(): Expr {
        var expr = this.multiplication()
        while (this.match(TokenType.PLUS, TokenType.MINUS)) {
            val operator = this.tokens[this.current - 1]
            val right = this.multiplication()
            expr = Expr.Binary(expr, operator, right)
        }
        return expr
    }

    private fun multiplication(): Expr {
        var expr = this.unary()
        while (this.match(TokenType.SLASH, TokenType.STAR)) {
            val operator = this.previous()
            val right = this.unary()
            expr = Expr.Binary(expr, operator, right)
        }
        return expr
    }

    private fun unary(): Expr {
        if (this.match(TokenType.BANG, TokenType.MINUS)) {
            val operator = this.previous()
            val right = this.unary()
            return Expr.Unary(operator, right)
        }
        return this.primary()
    }

    private fun primary(): Expr {
        return when {
            this.match(TokenType.FALSE) -> Expr.Literal(false)
            this.match(TokenType.TRUE) -> Expr.Literal(true)
            this.match(TokenType.NIL) -> Expr.Literal(null)
            this.match(TokenType.NUMBER, TokenType.STRING) -> {
                Expr.Literal(this.previous().literal)
            }
            this.match(TokenType.LEFT_PAREN) -> {
                val expr = this.expression()
                this.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression")
                Expr.Grouping(expr)
            }
            this.match(TokenType.IDENTIFIER) -> Expr.Variable(this.previous())
            else -> throw this.error(this.peek(), "Expect expression, got ${this.peek()}")
        }
    }

    private fun synchronize() {
        // Discard tokens until the end of the statement (when we can recover)
        this.advance()

        while (this.peek().type != TokenType.EOF) {
            if (this.previous().type == TokenType.SEMICOLON) return

            when (this.peek().type) {
                TokenType.CLASS, TokenType.FUN, TokenType.VAR, TokenType.FOR,
                TokenType.IF, TokenType.WHILE, TokenType.PRINT,
                TokenType.RETURN -> return
                else -> {
                }
            }
            this.advance()
        }
    }
}