// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::path::Path;
use std::process::Command;

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
// handle: tauri::AppHandle,
fn image_to_text(handle: tauri::AppHandle, image: String) -> String {
    println!("hello from tauri!");

    let image = image.trim();
    println!("{}", &image);
    // get external resources:
    let path_python = handle
        .path_resolver()
        .resolve_resource("../src-py/predict.py")
        .expect("failed to resolve python script");

    // 1. Specify Python version
    let python_version = "3.10.13";

    // 2. Check Python installation
    let python_check_output = Command::new("python3")
        .arg("--version")
        .output()
        .expect("Failed to execute Python command");

    let python_output = String::from_utf8_lossy(&python_check_output.stdout);
    println!("python_output: {}", python_output);
    if !python_output.contains(python_version) {
        panic!("Python {} is not installed", python_version);
    }

    // 3. Activate virtual environment and install dependencies
    let venv_path = Path::new("../src-py/venv");
    if !venv_path.exists() {
        // Create virtual environment
        let create_venv_output = Command::new("python3")
            .arg("-m")
            .arg("venv")
            .arg("../src-py/venv")
            .output()
            .expect("Failed to create virtual environment");

        if !create_venv_output.status.success() {
            panic!(
                "Failed to create virtual environment: {}",
                String::from_utf8_lossy(&create_venv_output.stderr)
            );
        }

        // Activate virtual environment
        let activate_venv_output = Command::new("sh")
            .arg("-c")
            .arg("source ../src-py/venv/bin/activate")
            .output()
            .expect("Failed to activate virtual environment");
        if !activate_venv_output.status.success() {
            panic!(
                "Failed to activate virtual environment: {}",
                String::from_utf8_lossy(&activate_venv_output.stderr)
            );
        }

        // Install dependencies
        let pip_install_output = Command::new("pip")
            .arg("install")
            .arg("-r")
            .arg("requirements.txt")
            .output()
            .expect("Failed to install dependencies");

        if !pip_install_output.status.success() {
            panic!(
                "Failed to install dependencies: {}",
                String::from_utf8_lossy(&pip_install_output.stderr)
            );
        }
    } else {
        // Activate virtual environment
        let activate_venv_output = Command::new("source")
            .arg("../src-py/venv/bin/activate")
            .output()
            .expect("Failed to activate virtual environment");

        if !activate_venv_output.status.success() {
            panic!(
                "Failed to activate virtual environment: {}",
                String::from_utf8_lossy(&activate_venv_output.stderr)
            );
        }
    }

    // 5. Call Python function from Rust
    // Your Python function call goes here

    let output = Command::new("python3")
        .arg(path_python)
        .arg(&image)
        .output();

    match output {
        Err(error) => error.to_string(),
        Ok(ok_output) => {
            let x = parse_py_output(String::from_utf8(ok_output.stdout).unwrap().as_str());
            println!("in main {}", x);
            x
        }
    }
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
    result.to_string()
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
