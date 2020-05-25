class LoxFunction(
    private val declaration: Stmt.Function,
    private val closure: Environment,
    private val isInitializer: Boolean
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
            if (this.isInitializer) return this.closure.getAt(0, "this")
            return returnValue.value
        }

        if (this.isInitializer) {
            return this.closure.getAt(0, "this")
        }
        return null
    }

    fun bind(instance: LoxInstance): LoxFunction {
        val environment = Environment(this.closure)
        environment.define("this", instance)
        return LoxFunction(this.declaration, environment, this.isInitializer)
    }

    override fun toString(): String {
        return "<fn ${this.declaration.name.lexeme}>"
    }
}