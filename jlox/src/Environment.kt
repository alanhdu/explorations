class Environment(val enclosing: Environment? = null) {
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

    fun getAt(distance: Int, name: String): Any? {
        val vals = this.ancestor(distance).values
        return vals.getValue(name)
    }

    fun assignAt(distance: Int, name: Token, value: Any?) {
        this.ancestor(distance).values[name.lexeme] = value
    }

    fun ancestor(distance: Int): Environment {
        var env = this
        for (i in 0 until distance) {
            env = env.enclosing!!
        }
        return env
    }

    override fun toString(): String {
        return "Environment(${this.values}, ${this.enclosing})"
    }

}