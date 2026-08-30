// Prevent Rust compiler from complaining about unused imports
#![allow(dead_code)]
#![allow(unused_imports)]

mod geometry;
mod translation;
mod inpainting;
mod render;
mod config;
mod database;

use tauri::{Manager, State};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageData {
    pub id: String,
    pub name: String,
    pub data: String, // base64 encoded
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessConfig {
    pub source_lang: String,
    pub target_lang: String,
    pub auto_inpaint: bool,
    pub preserve_style: bool,
    pub api_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessResult {
    pub id: String,
    pub status: String,
    pub output_image: Option<String>,
    pub error: Option<String>,
}

#[derive(Default)]
pub struct AppState {
    pub processing: Arc<Mutex<bool>>,
}

#[tauri::command]
async fn process_images(
    images: Vec<ImageData>,
    config: ProcessConfig,
    _state: State<'_, Arc<AppState>>,
) -> Result<Vec<ProcessResult>, String> {
    // This is where the actual processing will happen
    // For now, return a mock response
    
    let mut results = Vec::new();
    
    for image in images {
        results.push(ProcessResult {
            id: image.id,
            status: "completed".to_string(),
            output_image: None,
            error: None,
        });
    }
    
    Ok(results)
}

#[tauri::command]
fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

fn main() {
    tracing_subscriber::fmt::init();
    
    tauri::Builder::default()
        .manage(Arc::new(AppState::default()))
        .invoke_handler(tauri::generate_handler![
            process_images,
            get_version
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
