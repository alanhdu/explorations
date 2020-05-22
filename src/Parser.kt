class Parser(private val tokens: List<Token>) {
    private class ParseError : RuntimeException()

    // # of for/while loops we can break out of (one per function declaration)
    private val breakables = mutableListOf(0)
    private var current = 0    // which token we are parsing

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
            Lox.hadError = true
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
            this.match(TokenType.BREAK) -> this.breakStatement()
            this.match(TokenType.FOR) -> this.forStatement()
            this.match(TokenType.FUN) -> this.function("function")
            this.match(TokenType.IF) -> this.ifStatement()
            this.match(TokenType.LEFT_BRACE) -> Stmt.Block(this.block())
            this.match(TokenType.PRINT) -> this.printStatement()
            this.match(TokenType.RETURN) -> this.returnStatement()
            this.match(TokenType.WHILE) -> this.whileStatement()
            else -> this.expressionStatement()
        }
    }

    private fun breakableStatement(): Stmt {
        val s = this.breakables.size
        this.breakables[s - 1] = this.breakables[s - 1] + 1
        val stmt = this.statement()
        this.breakables[s - 1] = this.breakables[s - 1] - 1
        return stmt
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

    private fun printStatement(): Stmt.Print {
        val value = this.expression()
        this.consume(TokenType.SEMICOLON, "Expect ';' after value")
        return Stmt.Print(value)
    }

    private fun ifStatement(): Stmt.If {
        this.consume(TokenType.LEFT_PAREN, "Expect ( after if")
        val cond = this.expression()
        this.consume(TokenType.RIGHT_PAREN, "Expect ) after if condition")

        val thenBranch = this.statement()
        val elseBranch = if (this.match(TokenType.ELSE)) {
            this.statement()
        } else null

        return Stmt.If(cond, thenBranch, elseBranch)
    }

    private fun whileStatement(): Stmt.While {
        this.consume(TokenType.LEFT_PAREN, "Expect ( after while")
        val cond = this.expression()
        this.consume(TokenType.RIGHT_PAREN, "Expect ) after while condition")

        return Stmt.While(cond, this.breakableStatement())
    }

    private fun forStatement(): Stmt {
        this.consume(TokenType.LEFT_PAREN, "Expect ( after for")
        val initializer = when {
            this.match(TokenType.SEMICOLON) -> null
            this.match(TokenType.VAR) -> this.varDeclaration()
            else -> this.expressionStatement()
        }

        val condition = when {
            this.check(TokenType.SEMICOLON) -> Expr.Literal(true)
            else -> this.expression()
        }
        this.consume(TokenType.SEMICOLON, "Expect ; after loop condition")

        val increment = when {
            this.check(TokenType.RIGHT_PAREN) -> null
            else -> this.expression()
        }
        this.consume(TokenType.RIGHT_PAREN, "Expect ) after for clauses")

        // Desugar into a while loop
        var body = this.breakableStatement()
        if (increment != null) {
            body = Stmt.Block(listOf(body, Stmt.Expression(increment)))
        }
        body = Stmt.While(condition, body)
        if (initializer != null) {
            body = Stmt.Block(listOf(initializer, body))
        }

        return body
    }

    private fun breakStatement(): Stmt.Break {
        if (this.breakables.last() > 0) {
            this.consume(TokenType.SEMICOLON, "Expected ; after break")
            return Stmt.Break()
        } else {
            throw this.error(this.previous(), "break found in bad context")
        }
    }

    private fun function(kind: String): Stmt.Function {
        val name = this.consume(TokenType.IDENTIFIER, "Expect $kind name")

        // Construct Arguments
        this.consume(TokenType.LEFT_PAREN, "Expect ( after $kind name")
        val params = ArrayList<Token>()
        if (!this.check(TokenType.RIGHT_PAREN)) {
            do {
                params.add(this.consume(TokenType.IDENTIFIER, "Expect parameter name"))
            } while (this.match(TokenType.COMMA))
        }
        this.consume(TokenType.RIGHT_PAREN, "Expect ) after parameters")

        // Body
        this.consume(TokenType.LEFT_BRACE, "Expect { before $kind body")

        this.breakables.add(0)
        val body = this.block()
        this.breakables.removeAt(this.breakables.size - 1)

        return Stmt.Function(name, params, body)
    }

    private fun returnStatement(): Stmt.Return {
        if (this.breakables.size == 1) {
            throw this.error(this.previous(), "return out of function declaration")
        }

        val keyword = this.previous()
        val value = if (this.check(TokenType.SEMICOLON)) {
            null
        } else {
            this.expression()
        }

        this.consume(TokenType.SEMICOLON, "Expected ; after return value")
        return Stmt.Return(keyword, value)
    }

    private fun expressionStatement(): Stmt.Expression {
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
        return this.call()
    }

    private fun call(): Expr {
        var expr = this.primary()

        while (true) {
            if (this.match(TokenType.LEFT_PAREN)) {
                expr = this.finishCall(expr)
            } else {
                break
            }
        }
        return expr
    }

    private fun finishCall(callee: Expr): Expr.Call {
        val args = ArrayList<Expr>()
        if (!this.check(TokenType.RIGHT_PAREN)) {
            do {
                args.add(this.expression())
            } while (this.match(TokenType.COMMA))
        }
        if (args.size >= 255) {
            this.error(this.peek(), "Cannot have more than 255 arguments (got ${args.size})")
        }

        val paren = this.consume(TokenType.RIGHT_PAREN, "Expected ) after arguments")
        return Expr.Call(callee, paren, args)
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