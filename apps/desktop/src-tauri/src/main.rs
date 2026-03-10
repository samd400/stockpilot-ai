// StockPilot Desktop — Tauri main entry with native printing commands.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use base64::Engine as _;
use std::io::Write;
use std::net::TcpStream;
use std::time::Duration;

/// Send raw ESC/POS bytes to a network printer via TCP.
#[tauri::command]
fn print_raw(ip: String, port: u16, data_b64: String) -> Result<String, String> {
    let bytes = base64::engine::general_purpose::STANDARD
        .decode(&data_b64)
        .map_err(|e| format!("Base64 decode error: {}", e))?;

    let addr = format!("{}:{}", ip, port);
    let mut stream = TcpStream::connect_timeout(
        &addr.parse().map_err(|e| format!("Invalid address: {}", e))?,
        Duration::from_secs(5),
    )
    .map_err(|e| format!("Connection failed to {}: {}", addr, e))?;

    stream
        .write_all(&bytes)
        .map_err(|e| format!("Write failed: {}", e))?;

    stream.flush().map_err(|e| format!("Flush failed: {}", e))?;

    Ok(format!("Sent {} bytes to {}", bytes.len(), addr))
}

/// Open cash drawer via ESC/POS command on network printer.
#[tauri::command]
fn open_cash_drawer(ip: String, port: u16) -> Result<String, String> {
    // ESC p 0 25 255 — standard cash drawer kick command
    let cmd: Vec<u8> = vec![0x1b, 0x70, 0x00, 0x19, 0xff];
    let addr = format!("{}:{}", ip, port);
    let mut stream = TcpStream::connect_timeout(
        &addr.parse().map_err(|e| format!("Invalid address: {}", e))?,
        Duration::from_secs(5),
    )
    .map_err(|e| format!("Connection failed: {}", e))?;

    stream
        .write_all(&cmd)
        .map_err(|e| format!("Write failed: {}", e))?;

    Ok(format!("Cash drawer opened at {}", addr))
}

/// Check if a network printer is reachable.
#[tauri::command]
fn check_printer(ip: String, port: u16) -> Result<bool, String> {
    let addr = format!("{}:{}", ip, port);
    match TcpStream::connect_timeout(
        &addr.parse().map_err(|e| format!("Invalid address: {}", e))?,
        Duration::from_secs(3),
    ) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            print_raw,
            open_cash_drawer,
            check_printer
        ])
        .run(tauri::generate_context!())
        .expect("error while running StockPilot Desktop");
}
