// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn image_to_text(handle: tauri::AppHandle, image_data: String) -> Result<String, String> {
    // get external resources:
    let path_python = handle.path_resolver()
        .resolve_resource("../src-py/predict.py")
        .expect("failed to resolve python script");
    let path_model = handle.path_resolver()
        .resolve_resource("../src-py/models/50_epochs.keras")
        .expect("failed to resolve keras model");
    let path_chars = handle.path_resolver()
        .resolve_resource("../src-py/models/characters.txt")
        .expect("failed to resolve character file");

    let output = Command::new("python3")
        .arg(path_python)
        .arg("TODO/imgfile")
        .arg(path_model)
        .arg(path_chars)
        .output()
        .expect("failed to execute Python code.");

    Ok("placeholder".to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![image_to_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
