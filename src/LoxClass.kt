class LoxClass(
    val name: String,
    private val superclass: LoxClass?,
    private val methods: Map<String, LoxFunction>
) : LoxCallable {
    override fun arity(): Int {
        val initializer = this.findMethod("init")
        return initializer?.arity() ?: 0
    }

    override fun call(interpreter: Interpreter, args: List<Any?>): Any? {
        val instance = LoxInstance(this)
        val initializer = this.findMethod("init")
        initializer?.bind(instance)?.call(interpreter, args)
        return instance
    }

    fun findMethod(name: String): LoxFunction? {
        if (this.methods.containsKey(name)) return this.methods[name]
        if (this.superclass != null) return this.superclass.findMethod(name)
        return null
    }

    override fun toString(): String {
        return "<class ${this.name}>"
    }
}