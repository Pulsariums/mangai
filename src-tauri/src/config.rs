//! Configuration module for application settings
//! Handles loading and validating configuration from YAML/JSON files

use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub api_keys: Vec<String>,
    pub source_language: String,
    pub target_language: String,
    pub inpainting: InpaintConfig,
    pub render: RenderConfig,
    pub output: OutputConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InpaintConfig {
    pub algorithm: String,
    pub dilate_iterations: u32,
    pub preserve_edges: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RenderConfig {
    pub font_family: String,
    pub default_font_size: f32,
    pub outline_width: f32,
    pub auto_shrink: bool,
    pub max_shrink_factor: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputConfig {
    pub output_dir: String,
    pub debug_dir: String,
    pub save_masks: bool,
    pub save_debug_images: bool,
    pub format: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        AppConfig {
            api_keys: vec![],
            source_language: "ja".to_string(),
            target_language: "en".to_string(),
            inpainting: InpaintConfig {
                algorithm: "lama".to_string(),
                dilate_iterations: 2,
                preserve_edges: true,
            },
            render: RenderConfig {
                font_family: "Arial".to_string(),
                default_font_size: 16.0,
                outline_width: 2.0,
                auto_shrink: true,
                max_shrink_factor: 0.5,
            },
            output: OutputConfig {
                output_dir: "./output".to_string(),
                debug_dir: "./output/debug".to_string(),
                save_masks: true,
                save_debug_images: true,
                format: "png".to_string(),
            },
        }
    }
}

impl AppConfig {
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> Result<Self, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(path)?;
        let config: AppConfig = serde_yaml::from_str(&content)?;
        Ok(config)
    }
    
    pub fn save_to_file<P: AsRef<Path>>(&self, path: P) -> Result<(), Box<dyn std::error::Error>> {
        let content = serde_yaml::to_string(self)?;
        std::fs::write(path, content)?;
        Ok(())
    }
    
    pub fn validate(&self) -> Result<(), String> {
        if self.api_keys.is_empty() {
            return Err("At least one API key is required".to_string());
        }
        
        if self.render.max_shrink_factor <= 0.0 || self.render.max_shrink_factor > 1.0 {
            return Err("max_shrink_factor must be between 0 and 1".to_string());
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_default_config() {
        let config = AppConfig::default();
        assert_eq!(config.source_language, "ja");
        assert_eq!(config.target_language, "en");
        assert_eq!(config.inpainting.dilate_iterations, 2);
    }
    
    #[test]
    fn test_validate_config() {
        let mut config = AppConfig::default();
        config.api_keys.push("test_key".to_string());
        assert!(config.validate().is_ok());
    }
}
