use serde::{Deserialize, Serialize};
use reqwest::Client;
use serde_json::json;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageData {
    pub id: String,
    pub name: String,
    pub data: String,
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
pub struct TextBlock {
    pub id: String,
    pub original_text: String,
    pub translated_text: String,
    pub bbox: [i32; 4],
    pub angle: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessResult {
    pub success: bool,
    pub message: String,
    pub blocks: Vec<TextBlock>,
}

async fn call_gemini_api(
    api_key: &str,
    image_data: &str,
    source_lang: &str,
    target_lang: &str,
) -> Result<Vec<TextBlock>, String> {
    let client = Client::new();
    
    // Gemini 1.5 Flash Lite model endpoint
    let url = format!(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={}",
        api_key
    );
    
    // Base64 data URL'den base64 kısmını çıkar
    let base64_image = image_data
        .strip_prefix("data:image/png;base64,")
        .or_else(|| image_data.strip_prefix("data:image/jpeg;base64,"))
        .unwrap_or(image_data);
    
    let prompt = format!(
        r#"You are a manga/manhwa translation assistant. Analyze this image and:
1. Detect all text bubbles and their positions
2. Extract the {} text from each bubble
3. Translate it to {}
4. Return JSON array with: id, original_text, translated_text, bbox [x,y,width,height], angle (degrees)

Return ONLY valid JSON array, no markdown or explanation."#,
        source_lang, target_lang
    );
    
    let payload = json!({
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": base64_image}}
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    });
    
    let response = client
        .post(&url)
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("API request failed: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }
    
    let result: serde_json::Value = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    // Parse Gemini response
    let candidates = result["candidates"]
        .as_array()
        .ok_or("No candidates in response")?;
    
    if candidates.is_empty() {
        return Err("Empty response from API".to_string());
    }
    
    let content = &candidates[0]["content"]["parts"][0]["text"];
    let text = content.as_str().unwrap_or("{}");
    
    // Remove markdown code blocks if present
    let clean_json = text
        .trim_start_matches("```json")
        .trim_start_matches("```")
        .trim_end_matches("```")
        .trim();
    
    let blocks: Vec<TextBlock> = serde_json::from_str(clean_json)
        .map_err(|e| format!("Failed to parse JSON: {}. Response: {}", e, text))?;
    
    Ok(blocks)
}

#[tauri::command]
async fn process_images(
    images: Vec<ImageData>,
    config: ProcessConfig,
) -> Result<ProcessResult, String> {
    tracing::info!("Processing {} images", images.len());
    
    if images.is_empty() {
        return Ok(ProcessResult {
            success: false,
            message: "No images to process".to_string(),
            blocks: vec![],
        });
    }
    
    // Process first image as demo
    let first_image = &images[0];
    
    match call_gemini_api(&config.api_key, &first_image.data, &config.source_lang, &config.target_lang).await {
        Ok(blocks) => {
            tracing::info!("Successfully detected {} text blocks", blocks.len());
            Ok(ProcessResult {
                success: true,
                message: format!("Processed {} images, found {} text blocks", 
                    images.len(), blocks.len()),
                blocks,
            })
        }
        Err(e) => {
            tracing::error!("API call failed: {}", e);
            Err(e)
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt::init();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![process_images])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
