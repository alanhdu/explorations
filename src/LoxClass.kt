class LoxClass(val name: String) : LoxCallable {
    override fun arity(): Int {
        return 0
    }

    override fun call(interpreter: Interpreter, args: List<Any?>): Any? {
        return LoxInstance(this)
    }

    override fun toString(): String {
        return "<class ${this.name}>"
    }
}