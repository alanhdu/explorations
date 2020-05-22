val keywords = mapOf(
    "and" to TokenType.AND,
    "class" to TokenType.CLASS,
    "else" to TokenType.ELSE,
    "false" to TokenType.FALSE,
    "for" to TokenType.FOR,
    "fun" to TokenType.FUN,
    "if" to TokenType.IF,
    "nil" to TokenType.NIL,
    "or" to TokenType.OR,
    "print" to TokenType.PRINT,
    "return" to TokenType.RETURN,
    "super" to TokenType.SUPER,
    "this" to TokenType.THIS,
    "true" to TokenType.TRUE,
    "var" to TokenType.VAR,
    "while" to TokenType.WHILE
)

class Scanner(private val source: String) {
    private val tokens: MutableList<Token> = ArrayList()
    private var start = 0
    private var current = 0
    private var line = 1

    fun scanTokens(): List<Token> {
        while (!this.isAtEnd()) {
            this.start = current
            this.scanToken()
        }

        this.tokens.add(Token(TokenType.EOF, "", null, line))
        return this.tokens
    }

    private fun isAtEnd(): Boolean {
        return this.current >= this.source.length
    }

    private fun scanToken() {
        when (val c = this.advance()) {
            '(' -> addToken(TokenType.LEFT_PAREN)
            ')' -> addToken(TokenType.RIGHT_PAREN)
            '{' -> addToken(TokenType.LEFT_BRACE)
            '}' -> addToken(TokenType.RIGHT_BRACE)
            ',' -> addToken(TokenType.COMMA)
            '.' -> addToken(TokenType.DOT)
            '-' -> addToken(TokenType.MINUS)
            '+' -> addToken(TokenType.PLUS)
            ';' -> addToken(TokenType.SEMICOLON)
            '*' -> addToken(TokenType.STAR)
            '!' -> addToken(
                if (this.match('=')) {
                    TokenType.BANG_EQUAL
                } else {
                    TokenType.BANG
                }
            )
            '=' -> addToken(
                if (this.match('=')) {
                    TokenType.EQUAL_EQUAL
                } else {
                    TokenType.EQUAL
                }
            )
            '<' -> addToken(
                if (this.match('=')) {
                    TokenType.LESS_EQUAL
                } else {
                    TokenType.LESS
                }
            )
            '>' -> addToken(
                if (this.match('=')) {
                    TokenType.GREATER_EQUAL
                } else {
                    TokenType.GREATER
                }
            )
            '/' -> {
                when {
                    this.match('/') -> {
                        while (peek() != '\n' && !this.isAtEnd()) {
                            this.advance()
                        }
                    }
                    this.match('*') -> this.blockComment()
                    else -> this.addToken(TokenType.SLASH)
                }
            }
            ' ', '\r', '\t' -> {
            }
            '\n' -> this.line++
            '"' -> this.string()
            in '0'..'9' -> this.number()
            in 'a'..'z', in 'A'..'Z', '_' -> this.identifier()
            else -> {
                Lox.error(this.line, "Unexpected character $c")
            }
        }
    }

    private fun advance(): Char {
        this.current++
        return this.source[this.current - 1]
    }

    private fun addToken(type: TokenType) {
        this.addToken(type, null)
    }

    private fun addToken(type: TokenType, literal: Any?) {
        val text = source.substring(this.start, this.current)
        this.tokens.add(Token(type, text, literal, this.line))
    }

    private fun match(expected: Char): Boolean {
        if (this.isAtEnd()) return false
        if (this.source[this.current] != expected) return false

        this.current++
        return true
    }

    private fun peek(): Char {
        if (this.isAtEnd()) return '\u0000'
        return this.source[this.current]
    }

    private fun peekNext(): Char {
        if (this.current + 1 >= this.source.length) return '\u0000'
        return this.source[this.current + 1]
    }

    private fun string() {
        while (this.peek() != '"' && !this.isAtEnd()) {
            if (this.peek() == '\n') this.line++
            this.advance()
        }

        // Unterminated string
        if (this.isAtEnd()) {
            Lox.error(line, "Unterminated string")
            return
        }

        // The closing "
        this.advance()

        // +/- 1 to trim off quotes
        val value = this.source.substring(this.start + 1, this.current - 1)
        this.addToken(TokenType.STRING, value)
    }

    private fun number() {
        while (this.peek().isDigit()) this.advance()

        if (this.peek() == '.' && this.peekNext().isDigit()) {
            this.advance() // consume the .
            while (this.peek().isDigit()) this.advance()
        }
        val value = this.source.substring(this.start, this.current).toDouble()
        this.addToken(TokenType.NUMBER, value)
    }

    private fun identifier() {
        while (this.peek().isLetterOrDigit() || this.peek() == '_') {
            this.advance()
        }
        // Check if identifier is a reserved keyword
        val text = this.source.substring(this.start, this.current)
        val type = keywords.getOrDefault(text, TokenType.IDENTIFIER)
        this.addToken(type)
    }

    private fun blockComment() {
        var level = 1

        while (level != 0) {
            when (this.peek()) {
                '/' -> if (this.peekNext() == '*') {
                    this.advance()
                    this.advance()
                    level += 1
                }
                '*' -> if (this.peekNext() == '/') {
                    level -= 1
                    this.advance()
                    this.advance()
                }
                '\n' -> this.line++
                else -> this.advance()
            }
            if (this.isAtEnd() && level != 0) {
                Lox.error(this.line, "Unbalanced /* ... */ block comment")
                return
            }
        }
    }
}