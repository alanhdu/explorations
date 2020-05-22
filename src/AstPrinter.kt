class AstPrinter : Expr.Visitor<String> {
    fun print(expr: Expr): String {
        return expr.accept(this)
    }

    private fun parenthesize(name: String, vararg exprs: Expr): String {
        val args = exprs.joinToString(" ", transform = { this.print(it) })
        return "($name $args)"
    }

    override fun visitBinaryExpr(expr: Expr.Binary): String {
        return parenthesize(expr.operator.lexeme, expr.left, expr.right)
    }

    override fun visitGroupingExpr(expr: Expr.Grouping): String {
        return parenthesize("group", expr.expression)
    }

    override fun visitLiteralExpr(expr: Expr.Literal): String {
        return when (expr.value) {
            null -> "nil"
            is String -> "\"${expr.value}\""
            else -> expr.toString()
        }
    }

    override fun visitUnaryExpr(expr: Expr.Unary): String {
        return parenthesize(expr.operator.lexeme, expr.right)
    }

    override fun visitVariableExpr(expr: Expr.Variable): String {
        return "(${expr.name.lexeme} =)"
    }

    override fun visitAssignExpr(expr: Expr.Assign): String {
        return "(${expr.name.lexeme} = ${parenthesize("value", expr.value)})"
    }

    override fun visitLogicalExpr(expr: Expr.Logical): String {
        return parenthesize(expr.operator.lexeme, expr.left, expr.right)
    }
}