val NUM_ERR_MSG = "Operands must be two numbers"

class Interpreter : Expr.Visitor<Any?> {
    fun interpret(expr: Expr) {
        try {
            val value = this.evaluate(expr)
            println(this.stringify(value))
        } catch (error: RuntimeError) {
            Lox.runtimeError(error)
        }
    }

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

    private fun evaluate(expr: Expr): Any? {
        return expr.accept(this)
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
}