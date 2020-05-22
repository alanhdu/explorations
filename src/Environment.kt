class Environment(private val enclosing: Environment? = null) {
    private val values: HashMap<String, Any?> = HashMap()

    fun define(name: String, value: Any?) {
        this.values[name] = value
    }

    fun assign(name: Token, value: Any?) {
        if (values.containsKey(name.lexeme)) {
            this.values[name.lexeme] = value
            return
        } else if (this.enclosing != null) {
            this.enclosing.assign(name, value)
            return
        }
        throw RuntimeError(name, "Undefined variable '${name.lexeme}'.")
    }

    fun get(name: Token): Any? {
        if (this.values.containsKey(name.lexeme)) {
            return this.values[name.lexeme]
        } else if (this.enclosing != null) {
            return this.enclosing.get(name)
        }
        throw RuntimeError(name, "Undefined variable '${name.lexeme}'.")
    }
}