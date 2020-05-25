class LoxClass(private val name: String) {

    override fun toString(): String {
        return "<class ${this.name}>"
    }
}