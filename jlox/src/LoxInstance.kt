class LoxInstance(private val klass: LoxClass) {
    private val fields: MutableMap<String, Any?> = HashMap()
    fun get(name: Token): Any? {
        if (this.fields.containsKey(name.lexeme)) {
            return this.fields[name.lexeme]; }
        val method = klass.findMethod(name.lexeme)
        if (method != null) return method.bind(this)

        throw RuntimeError(name, "Undefined property ${name.lexeme}")
    }

    fun set(name: Token, value: Any?) {
        this.fields[name.lexeme] = value
    }

    override fun toString(): String {
        return "<instanceof ${klass.name}>"
    }
}