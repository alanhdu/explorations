use std::env;
use std::io::Write;
use std::io;
use std::process::Command;
use std::collections::VecDeque;

fn cd(args: &Vec<&str>) {
    if args.len() != 1 {
        println!("Error: cd takes exactly one arg");
        return;
    }

    let new = env::set_current_dir(args[0]);
    if !new.is_ok() {
        println!("Error: directory not found");
    }
}

fn pwd(args: &Vec<&str>) {
    match args.len() {
        0 => println!("{}", env::current_dir().unwrap().display()),
        _ => println!("Error: pwd takes no arguments"),
    };
}

fn path_add(path: &str, dir: &str) {
    if path.split(":").any(|x| x == dir) {
        return;
    } else if path.is_empty() {
        env::set_var("PATH", dir)
    } else {
        env::set_var("PATH", path.to_owned() + ":" + dir)
    }
}

fn path_remove(path: &str, dir: &str) {
    // why is to_owned needed here?
    let new_path = path.split(":")
                       .filter(|x| x.to_owned() != dir)
                       .collect::<Vec<&str>>()
                       .join(":");
    env::set_var("PATH", new_path);
}

fn path(args: &Vec<&str>) {
    match env::var("PATH") {
        Err(e) => println!("Could not get PATH: {}", e),
        Ok(path) => match args.len() {
            0 => println!("{}", path),
            2 => match args[0] {
                "+" => path_add(&path, args[1]),
                "-" => path_remove(&path, args[1]),
                _ => println!("Error: path usage: path [+/- dir]"),
            },
            _ => println!("Error: path usage: path [+/- dir]"),
        },
    }
}

fn shell_exec(command: &str, args: &Vec<&str>) {
    match Command::new(command).args(args).spawn() {
        Err(e) => println!("error: {}", e),
        Ok(mut child) => match child.wait() {
            Err(e) => println!("error: {}", e),
            _ => {}
        },
    }
}

fn shell_history(args: &Vec<&str>, history: &mut VecDeque<String>) {
    match args.len() {
        0 => for (i, s) in history.iter().enumerate() {
            println!("{} {}", i, s);
        },
        1 => match args[0] {
            "-c" => history.clear(),
            s => match s.parse() {
                Err(_) => println!("Error: history usage: history [-c]/[%d]"),
                Ok(i) => {
                    if i >= history.len() {
                        println!("Error: arg out of bounds");
                    } else {
                        eval(&history[i].clone(), history);
                    }
                }
            },
        },
        _ => println!("Error: history usage: history [-c]/[%d]"),
    }
}

fn eval(input: &String, history: &mut VecDeque<String>) -> bool {
    let mut args = input.trim().split_whitespace();

    if let Some(command) = args.next() {
        let other_args = args.collect::<Vec<&str>>();

        if command != "history" {
            history.push_back(input.trim().clone().to_owned());
        }
        match command {
            "exit" => return true,
            "pwd" => pwd(&other_args),
            "cd" => cd(&other_args),
            "path" => path(&other_args),
            "history" => shell_history(&other_args, history),
            _ => shell_exec(command, &other_args),
        }
    }

    false
}

fn main() {
    env::set_var("PATH", "");
    let mut history: VecDeque<String> = VecDeque::with_capacity(100);
    loop {
        print!("$");
        io::stdout()
            .flush()
            .ok()
            .expect("Failed to flush");

        let mut input = String::new();
        io::stdin()
            .read_line(&mut input)
            .ok()
            .expect("Failed to read line");

        if eval(&input, &mut history) {
            break;
        }
    }
}
