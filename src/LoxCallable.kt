interface LoxCallable {
    fun arity(): Int
    fun call(interpreter: Interpreter, args: List<Any?>): Any?
}