import java.io.PrintWriter
import kotlin.system.exitProcess

fun defineAst(
    outputDir: String, baseName: String, types: Map<String, Map<String, String>>
) {
    val path = "$outputDir/$baseName.kt"
    val writer = PrintWriter(path, "UTF-8")
    writer.println("abstract class $baseName {")

    defineVisitor(writer, baseName, types)
    writer.println("  abstract fun <R> accept(visitor: Visitor<R>): R;")

    for ((name, fields) in types) {
        defineType(writer, baseName, name, fields)
    }
    writer.println("}")
    writer.close()
}

fun defineVisitor(
    writer: PrintWriter, baseName: String, types: Map<String, Map<String, String>>
) {
    writer.println("  interface Visitor<R> {")
    for (typeName in types.keys) {
        val funcName = "visit$typeName$baseName"
        val args = "${baseName.toLowerCase()}: $typeName"
        writer.println("    fun $funcName($args): R;")
    }
    writer.println("  }")
}

fun defineType(
    writer: PrintWriter,
    baseName: String,
    className: String,
    types: Map<String, String>
) {
    val fields = types
        .map { "val ${it.key}: ${it.value}" }
        .joinToString(", ")
    writer.println(
        """
        class $className($fields) : $baseName() {
            override fun <R> accept(visitor: Visitor<R>): R {
                return visitor.visit$className$baseName(this)
            }
        }
    """.trimIndent()
    )
}

// main
if (args.size != 1) {
    System.err.println("Usage: generate_ast <output directory>")
    exitProcess(64)
}
val outputDir = args[0]
defineAst(
    outputDir, "Expr", mapOf(
        "Assign" to mapOf("name" to "Token", "value" to "Expr"),
        "Binary" to mapOf("left" to "Expr", "operator" to "Token", "right" to "Expr"),
        "Call" to mapOf("callee" to "Expr", "paren" to "Token", "args" to "List<Expr>"),
        "Get" to mapOf("obj" to "Expr", "name" to "Token"),
        "Grouping" to mapOf("expression" to "Expr"),
        "Literal" to mapOf("value" to "Any?"),
        "Logical" to mapOf("left" to "Expr", "operator" to "Token", "right" to "Expr"),
        "Set" to mapOf("obj" to "Expr", "name" to "Token", "value" to "Expr"),
        "Unary" to mapOf("operator" to "Token", "right" to "Expr"),
        "Variable" to mapOf("name" to "Token")
    )
)
defineAst(
    outputDir, "Stmt", mapOf(
        "Break" to mapOf(),
        "Block" to mapOf("statements" to "List<Stmt>"),
        "Class" to mapOf("name" to "Token", "methods" to "List<Stmt.Function>"),
        "Expression" to mapOf("expr" to "Expr"),
        "Function" to mapOf("name" to "Token", "params" to "List<Token>", "body" to "List<Stmt>"),
        "If" to mapOf("condition" to "Expr", "thenBranch" to "Stmt", "elseBranch" to "Stmt?"),
        "Print" to mapOf("expr" to "Expr"),
        "Return" to mapOf("keyword" to "Token", "value" to "Expr?"),
        "Var" to mapOf("name" to "Token", "initializer" to "Expr?"),
        "While" to mapOf("condition" to "Expr", "body" to "Stmt")
    )
)
