import java.io.BufferedReader
import java.io.InputStreamReader
import java.nio.charset.Charset
import java.nio.file.Files
import java.nio.file.Paths
import kotlin.system.exitProcess


object Lox {
    private var hadError = false

    fun runFile(path: String) {
        val bytes = Files.readAllBytes(Paths.get(path))
        val s = String(bytes, Charset.defaultCharset())
        exec(s)
        if (hadError) {
            exitProcess(65)
        }
    }

    fun runPrompt() {
        val input = InputStreamReader(System.`in`)
        val reader = BufferedReader(input)

        while (true) {
            print("> ")
            exec(reader.readLine())
            hadError = false
        }
    }

    private fun exec(source: String) {
        val scanner = Scanner(source)
        val tokens = scanner.scanTokens()

        println(tokens)
        val parser = Parser(tokens)
        val expr = parser.parse()
        if (hadError) return

        if (expr != null) {
            println(AstPrinter().print(expr))
        }
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