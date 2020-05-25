import java.util.*
import kotlin.collections.HashMap
import kotlin.collections.set

class Resolver(private val interpreter: Interpreter) : Expr.Visitor<Unit>, Stmt.Visitor<Unit> {
    private enum class FunctionType {
        NONE,
        FUNCTION
    }

    private val scopes: Stack<MutableMap<String, Boolean>> = Stack()
    private var currentFunction: FunctionType = FunctionType.NONE

    fun resolve(stmts: List<Stmt>) {
        for (stmt in stmts) this.resolve(stmt)
    }

    fun resolve(stmt: Stmt) {
        stmt.accept(this)
    }

    fun resolve(expr: Expr) {
        expr.accept(this)
    }

    private fun resolveLocal(expr: Expr, name: Token) {
        for ((i, scope) in scopes.reversed().withIndex()) {
            if (scope.containsKey(name.lexeme)) {
                this.interpreter.resolve(expr, i)
                return
            }
        }
    }

    private fun resolveFunction(func: Stmt.Function, type: FunctionType) {
        val enclosing = this.currentFunction
        this.currentFunction = type
        this.beginScope()
        for (param in func.params) {
            this.declare(param)
            this.define(param)
        }
        this.resolve(func.body)
        this.endScope()
        this.currentFunction = enclosing
    }

    private fun beginScope() {
        this.scopes.push(HashMap())
    }

    private fun endScope() {
        this.scopes.pop()
    }

    private fun declare(name: Token) {
        if (scopes.empty()) return
        val scope = scopes.peek()
        if (scope.containsKey(name.lexeme)) {
            Lox.error(name, "Variable with name ${name.lexeme} already declared in scope")
        }
        scope[name.lexeme] = false
    }

    private fun define(name: Token) {
        if (scopes.empty()) return
        scopes.peek()[name.lexeme] = true
    }

    override fun visitBreakStmt(stmt: Stmt.Break) {
    }

    override fun visitBlockStmt(stmt: Stmt.Block) {
        this.beginScope()
        this.resolve(stmt.statements)
        this.endScope()
    }

    override fun visitClassStmt(stmt: Stmt.Class) {
        this.declare(stmt.name)
        this.define(stmt.name)
    }

    override fun visitExpressionStmt(stmt: Stmt.Expression) {
        this.resolve(stmt.expr)
    }

    override fun visitFunctionStmt(stmt: Stmt.Function) {
        this.declare(stmt.name)
        this.define(stmt.name)
        this.resolveFunction(stmt, FunctionType.FUNCTION)
    }

    override fun visitIfStmt(stmt: Stmt.If) {
        this.resolve(stmt.condition)
        this.resolve(stmt.thenBranch)
        if (stmt.elseBranch != null) this.resolve(stmt.elseBranch)
    }

    override fun visitPrintStmt(stmt: Stmt.Print) {
        this.resolve(stmt.expr)
    }

    override fun visitReturnStmt(stmt: Stmt.Return) {
        if (this.currentFunction == FunctionType.NONE) {
            Lox.error(stmt.keyword, "Cannot return from top-level code.")
        }
        if (stmt.value != null) this.resolve(stmt.value)
    }

    override fun visitVarStmt(stmt: Stmt.Var) {
        this.declare(stmt.name)
        if (stmt.initializer != null) {
            this.resolve(stmt.initializer)
        }
        this.define(stmt.name)
    }

    override fun visitWhileStmt(stmt: Stmt.While) {
        this.resolve(stmt.condition)
        this.resolve(stmt.body)
    }

    override fun visitAssignExpr(expr: Expr.Assign) {
        this.resolve(expr.value)
        this.resolveLocal(expr, expr.name)
    }

    override fun visitBinaryExpr(expr: Expr.Binary) {
        this.resolve(expr.left)
        this.resolve(expr.right)
    }

    override fun visitCallExpr(expr: Expr.Call) {
        this.resolve(expr.callee)
        expr.args.forEach { this.resolve(it) }
    }

    override fun visitGetExpr(expr: Expr.Get) {
        this.resolve(expr.obj)
    }

    override fun visitGroupingExpr(expr: Expr.Grouping) {
        this.resolve(expr.expression)
    }

    override fun visitLiteralExpr(expr: Expr.Literal) {
    }

    override fun visitLogicalExpr(expr: Expr.Logical) {
        this.resolve(expr.left)
        this.resolve(expr.right)
    }

    override fun visitSetExpr(expr: Expr.Set) {
        this.resolve(expr.value)
        this.resolve(expr.obj)
    }

    override fun visitUnaryExpr(expr: Expr.Unary) {
        this.resolve(expr.right)
    }

    override fun visitVariableExpr(expr: Expr.Variable) {
        if (!scopes.empty() && scopes.peek()[expr.name.lexeme] == false) {
            Lox.error(expr.name, "Cannot read local variable name in its own initializer")
        }
        this.resolveLocal(expr, expr.name)
    }
}