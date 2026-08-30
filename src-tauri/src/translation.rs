//! Translation module using Gemini API
//! Handles API key rotation, rate limiting, and context-aware translation

use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranslationRequest {
    pub text_blocks: Vec<TextBlockInput>,
    pub source_lang: String,
    pub target_lang: String,
    pub glossary: Option<Vec<GlossaryEntry>>,
    pub context: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextBlockInput {
    pub id: String,
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlossaryEntry {
    pub source: String,
    pub target: String,
    pub notes: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranslationResponse {
    pub translations: Vec<TranslatedBlock>,
    pub usage: UsageInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranslatedBlock {
    pub id: String,
    pub original: String,
    pub translated: String,
    pub confidence: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageInfo {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

pub struct GeminiTranslator {
    client: Client,
    api_keys: Vec<String>,
    current_key_index: usize,
    base_url: String,
}

impl GeminiTranslator {
    pub fn new(api_keys: Vec<String>) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");
        
        Self {
            client,
            api_keys,
            current_key_index: 0,
            base_url: "https://generativelanguage.googleapis.com/v1beta".to_string(),
        }
    }
    
    pub fn rotate_key(&mut self) {
        if !self.api_keys.is_empty() {
            self.current_key_index = (self.current_key_index + 1) % self.api_keys.len();
        }
    }
    
    pub fn current_key(&self) -> Option<&String> {
        self.api_keys.get(self.current_key_index)
    }
    
    pub async fn translate(
        &self,
        request: TranslationRequest,
    ) -> Result<TranslationResponse, Box<dyn std::error::Error>> {
        // Placeholder implementation
        // In production, this would call Gemini API with proper error handling
        
        let mut translations = Vec::new();
        for block in request.text_blocks {
            translations.push(TranslatedBlock {
                id: block.id,
                original: block.text,
                translated: format!("[Translated: {}]", block.text),
                confidence: 0.95,
            });
        }
        
        Ok(TranslationResponse {
            translations,
            usage: UsageInfo {
                prompt_tokens: 100,
                completion_tokens: 150,
                total_tokens: 250,
            },
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_key_rotation() {
        let keys = vec!["key1".to_string(), "key2".to_string(), "key3".to_string()];
        let mut translator = GeminiTranslator::new(keys);
        
        assert_eq!(translator.current_key(), Some(&"key1".to_string()));
        translator.rotate_key();
        assert_eq!(translator.current_key(), Some(&"key2".to_string()));
        translator.rotate_key();
        assert_eq!(translator.current_key(), Some(&"key3".to_string()));
        translator.rotate_key();
        assert_eq!(translator.current_key(), Some(&"key1".to_string()));
    }
}
