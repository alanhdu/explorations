use std::collections::VecDeque;
use std::env;
use std::fs;
use std::io::Write;
use std::io;
use std::process::Command;

fn shell_cd(args: &Vec<&str>) {
    match args.len() {
        1 => match env::set_current_dir(args[0]) {
            Err(e) => println!("error: {}", e),
            Ok(_) => {},
        },
        _ => println!("Error: cd takes exactly one arg"),
    }
}

fn shell_pwd(args: &Vec<&str>) {
    match args.len() {
        0 => println!("{}", env::current_dir().unwrap().display()),
        _ => println!("Error: pwd takes no arguments"),
    };
}

fn path_add(path: &mut String, dir: &str) {
    if path.split(":").any(|x| x == dir) {
        return;
    } else if !path.is_empty() {
        path.push(':');
    }
    path.push_str(dir);
}

fn path_remove(path: &mut String, dir: &str) {
    // why is to_owned needed here?
    let new_path = path.split(":")
                       .filter(|x| x.to_owned() != dir)
                       .collect::<Vec<&str>>()
                       .join(":");
    path.clear();
    path.push_str(&new_path);
}

fn find_full_name(command: &str, path: &str) -> String {
    match command.chars().next() {
        Some('/') => command.to_owned(),
        None => command.to_owned(),
        Some(_) => {
            for part in path.split(":") {
                let full = part.to_owned() + "/" + command;
                if let Ok(file) = fs::metadata(&full) {
                    if file.is_file() {
                        return full.to_owned();
                    }
                }
            }
            command.to_owned()
        }
    }
}

fn shell_path(args: &Vec<&str>, path: &mut String) {
    match args.len() {
        0 => println!("{}", path),
        2 => match args[0] {
            "+" => path_add(path, args[1]),
            "-" => path_remove(path, args[1]),
            _ => println!("Error: path usage: path [+/- dir]"),
        },
        _ => println!("Error: path usage: path [+/- dir]"),
    }
}

fn shell_exec(command: &str, args: &Vec<&str>, path: &str) {
    let full_command = find_full_name(command, path);
    match Command::new(full_command).args(args).spawn() {
        Err(e) => println!("error: {}", e),
        Ok(mut child) => match child.wait() {
            Err(e) => println!("error: {}", e),
            _ => {}
        },
    }
}

fn shell_history(args: &Vec<&str>, history: &mut VecDeque<String>, path: &mut String) {
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
                        eval(&history[i].clone(), history, path);
                    }
                }
            },
        },
        _ => println!("Error: history usage: history [-c]/[%d]"),
    }
}

fn eval(input: &str, history: &mut VecDeque<String>, path: &mut String) -> bool {
    let mut args = input.trim().split_whitespace();

    if let Some(command) = args.next() {
        let other_args = args.collect::<Vec<&str>>();

        if command != "history" {
            history.push_back(input.trim().clone().to_owned());
        }
        match command {
            "exit" => return true,
            "pwd" => shell_pwd(&other_args),
            "cd" => shell_cd(&other_args),
            "path" => shell_path(&other_args, path),
            "history" => shell_history(&other_args, history, path),
            _ => shell_exec(command, &other_args, path),
        }
    }

    false
}

fn main() {
    env::set_var("PATH", "");
    let mut history: VecDeque<String> = VecDeque::with_capacity(100);
    let mut path = String::new();
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

        if eval(&input, &mut history, &mut path) {
            break;
        }
    }
}
