class LoxInstance(private val klass: LoxClass) {

    override fun toString(): String {
        return "<instanceof ${klass.name}>"
    }
}