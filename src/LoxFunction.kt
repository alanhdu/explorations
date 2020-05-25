class LoxFunction(
    private val declaration: Stmt.Function,
    private val closure: Environment
) : LoxCallable {
    override fun arity(): Int {
        return this.declaration.params.size
    }

    override fun call(interpreter: Interpreter, args: List<Any?>): Any? {
        val env = Environment(this.closure)
        for ((param, arg) in this.declaration.params.zip(args)) {
            env.define(param.lexeme, arg)
        }
        try {
            interpreter.executeBlock(this.declaration.body, env)
        } catch (returnValue: Return) {
            return returnValue.value
        }
        return null
    }

    override fun toString(): String {
        return "<fn ${this.declaration.name.lexeme}>"
    }
}