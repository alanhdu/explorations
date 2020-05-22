class Parser(private val tokens: List<Token>) {
    private class ParseError : RuntimeException()

    private var current = 0

    fun parse(): Expr? {
        return try {
            this.expression()
        } catch (error: ParseError) {
            null
        }
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

    private fun consume(type: TokenType, message: String) {
        if (this.check(type)) {
            this.advance()
            return
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

    private fun expression(): Expr {
        return this.equality()
    }

    private fun equality(): Expr {
        var expr = this.comparison()
        while (this.match(TokenType.BANG_EQUAL, TokenType.EQUAL)) {
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
            else -> throw this.error(this.peek(), "Expect expression")
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