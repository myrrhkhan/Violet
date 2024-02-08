// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
// handle: tauri::AppHandle,
fn image_to_text(handle: tauri::AppHandle, image: String) -> String {
    println!("hello from tauri!");
    println!("{}", image);
    // get external resources:
    let path_python = handle
        .path_resolver()
        .resolve_resource("../src-py/predict.py")
        .expect("failed to resolve python script");
    let path_model = handle
        .path_resolver()
        .resolve_resource("../src-py/models/50_epochs.keras")
        .expect("failed to resolve keras model");
    let path_chars = handle
        .path_resolver()
        .resolve_resource("../src-py/models/characters.txt")
        .expect("failed to resolve character file");

    // let path_python = "../src-py/predict.py";
    // let path_model = "../src-py/models/50_epochs.keras";
    // let path_chars = "../src-py/models/characters.txt";

    let output = Command::new("python3")
        .arg(path_python)
        .arg(path_chars)
        .arg(path_model)
        .arg(&image)
        .output();

    match output {
        Err(error) => return error.to_string(),
        Ok(ok_output) => {
            let x = parse_py_output(String::from_utf8(ok_output.stdout).unwrap().as_str());
            println!("in main {}", x);
            return x;
        }
    };
}

fn parse_py_output(output: &str) -> String {
    println!("output:");
    println!("{}", output);
    let spliced = output.split("\n");
    let vec = spliced.collect::<Vec<&str>>();
    for val in vec.iter() {
        println!("vec!");
        println!("{}", val);
    }
    let mut result = "";
    let mut diff = 1;
    while result.is_empty() {
        diff += 1;
        result = vec[vec.len() - diff];
        println!("result is {}", result);
    }
    let by_quotes = result.split("'").collect::<Vec<&str>>();
    result = by_quotes[1];
    return result.to_string();
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![image_to_text, greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
