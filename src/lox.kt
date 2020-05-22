import java.io.BufferedReader
import java.io.InputStreamReader
import java.nio.charset.Charset
import java.nio.file.Files
import java.nio.file.Paths
import kotlin.system.exitProcess


object Lox {
    private var hadError = false
    private var hadRuntimeError = false
    private val interpreter = Interpreter()

    fun runFile(path: String) {
        val bytes = Files.readAllBytes(Paths.get(path))
        val s = String(bytes, Charset.defaultCharset())
        run(s)
        if (hadError) exitProcess(65)
        if (hadRuntimeError) exitProcess(70)
    }

    fun runPrompt() {
        val input = InputStreamReader(System.`in`)
        val reader = BufferedReader(input)

        while (true) {
            print("> ")
            run(reader.readLine())
            hadError = false
        }
    }

    private fun run(source: String) {
        val scanner = Scanner(source)
        val tokens = scanner.scanTokens()

        val parser = Parser(tokens)
        val expr = parser.parse()
        if (expr == null) {
            hadError = true
            return
        } else if (hadError) return

        interpreter.interpret(expr)
    }

    fun error(line: Int, message: String) {
        report(line, "", message)
        hadError = true
    }

    fun error(token: Token, message: String) {
        if (token.type == TokenType.EOF) {
            report(token.line, " at end", message)
        } else {
            report(token.line, " at '${token.lexeme}'", message)
        }
    }

    private fun report(line: Int, where: String, message: String) {
        System.err.println("[line = $line ] Error$where: $message")
    }

    fun runtimeError(error: RuntimeError) {
        System.err.println(
            """
            ${error.message}
            [line ${error.token.line}]
        """.trimIndent()
        )
        hadRuntimeError = true
    }
}

fun main(args: Array<String>) {
    when {
        args.size > 1 -> {
            println("Usage: jlox [script]")
            exitProcess(64)
        }
        args.size == 1 -> {
            Lox.runFile(args[0])
        }
        else -> {
            Lox.runPrompt()
        }
    }
}