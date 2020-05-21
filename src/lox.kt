import java.io.BufferedReader
import java.io.InputStreamReader
import java.nio.charset.Charset
import java.nio.file.Files
import java.nio.file.Paths
import kotlin.system.exitProcess

var hadError = false

fun main(args: Array<String>) {
    when {
        args.size > 1 -> {
            println("Usage: jlox [script]")
            exitProcess(64)
        }
        args.size == 1 -> {
            runFile(args[0])
        }
        else -> {
            runPrompt()
        }
    }
}

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

fun exec(source: String) {
    val scanner = Scanner(source)
    val tokens = scanner.scanTokens()

    for (token in tokens) {
        println(token)
    }
}

fun error(line: Int, message: String) {
    report(line, "", message)
    hadError = true
}

fun report(line: Int, where: String, message: String) {
    System.err.println("[line = $line ] Error$where: $message")
}