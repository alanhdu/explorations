val NUM_ERR_MSG = "Operands must be two numbers"

class Interpreter : Expr.Visitor<Any?>, Stmt.Visitor<Unit> {
    private var env = Environment()

    fun interpret(stmts: List<Stmt>) {
        try {
            for (stmt in stmts) {
                this.execute(stmt)
            }
        } catch (error: RuntimeError) {
            Lox.runtimeError(error)
        }
    }

    private fun evaluate(expr: Expr): Any? {
        return expr.accept(this)
    }

    private fun execute(stmt: Stmt) {
        stmt.accept(this)
    }

    private fun isTruthy(expr: Any?): Boolean {
        return when (expr) {
            is Boolean -> expr
            null -> false
            else -> true
        }
    }

    private fun stringify(expr: Any?): String {
        return when (expr) {
            null -> "nil"
            is Double -> {
                var text = expr.toString()
                if (text.endsWith(".0")) {
                    text = text.substring(0, text.length - 2)
                }
                text
            }
            else -> expr.toString()
        }
    }


    // Expr.Visitor Implementation
    override fun visitBinaryExpr(expr: Expr.Binary): Any? {
        val left = this.evaluate(expr.left)
        val right = this.evaluate(expr.right)

        return when (expr.operator.type) {
            TokenType.MINUS -> {
                if (left is Double && right is Double) left - right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.SLASH -> {
                if (left is Double && right is Double) left / right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.STAR -> {
                if (left is Double && right is Double) left * right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.PLUS -> {
                if (left is Double && right is Double) left + right
                else if (left is String && right is String) left + right
                else throw RuntimeError(
                    expr.operator,
                    "Operands must be two numbers or two strings"
                )
            }
            TokenType.GREATER_EQUAL -> {
                if (left is Double && right is Double) left >= right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.GREATER -> {
                if (left is Double && right is Double) left > right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.LESS_EQUAL -> {
                if (left is Double && right is Double) left <= right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.LESS -> {
                if (left is Double && right is Double) left < right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.BANG_EQUAL -> left != right
            TokenType.EQUAL_EQUAL -> left == right
            else -> assert(false) { "Unreachable" }
        }
    }

    override fun visitGroupingExpr(expr: Expr.Grouping): Any? {
        return this.evaluate(expr.expression)
    }

    override fun visitLiteralExpr(expr: Expr.Literal): Any? {
        return expr.value
    }

    override fun visitUnaryExpr(expr: Expr.Unary): Any? {
        val right = this.evaluate(expr.right)

        return when (expr.operator.type) {
            TokenType.MINUS -> {
                if (right is Double) -right
                else throw RuntimeError(expr.operator, NUM_ERR_MSG)
            }
            TokenType.BANG -> !this.isTruthy(right)
            else -> assert(false) { "Unreachable" }
        }
    }

    override fun visitVariableExpr(expr: Expr.Variable): Any? {
        return this.env.get(expr.name)
    }

    override fun visitAssignExpr(expr: Expr.Assign): Any? {
        val value = this.evaluate(expr.value)
        this.env.assign(expr.name, value)
        return value
    }

    override fun visitLogicalExpr(expr: Expr.Logical): Any? {
        val left = this.evaluate(expr.left)

        return when (expr.operator.type) {
            TokenType.AND -> if (!isTruthy(left)) left else this.evaluate(expr.right)
            TokenType.OR -> if (isTruthy(left)) left else this.evaluate(expr.right)
            else -> assert(false) { "Unknown logical operator ${expr.operator}" }
        }
    }

    // Stmt.Visitor implementation
    override fun visitBlockStmt(stmt: Stmt.Block) {
        this.executeBlock(stmt.statements, Environment(this.env))
    }

    private fun executeBlock(stmts: List<Stmt>, env: Environment) {
        val prev = this.env
        try {
            this.env = env
            for (stmt in stmts) {
                this.execute(stmt)
            }
        } finally {
            this.env = prev
        }
    }

    override fun visitExpressionStmt(stmt: Stmt.Expression) {
        this.evaluate(stmt.expr)
    }

    override fun visitPrintStmt(stmt: Stmt.Print) {
        val value = this.evaluate(stmt.expr)
        println(this.stringify(value))
    }

    override fun visitVarStmt(stmt: Stmt.Var) {
        val value = if (stmt.initializer != null) {
            this.evaluate(stmt.initializer)
        } else null
        this.env.define(stmt.name.lexeme, value)
    }

    override fun visitIfStmt(stmt: Stmt.If) {
        val cond = this.evaluate(stmt.condition)
        if (this.isTruthy(cond)) {
            this.execute(stmt.thenBranch)
        } else if (stmt.elseBranch != null) {
            this.execute(stmt.elseBranch)
        }
    }
}