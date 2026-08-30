//! Database module for translation memory and glossary storage
//! Uses SQLite for local persistence

use rusqlite::{Connection, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranslationMemoryEntry {
    pub id: Option<i64>,
    pub source_text: String,
    pub translated_text: String,
    pub source_lang: String,
    pub target_lang: String,
    pub context: Option<String>,
    pub created_at: String,
    pub usage_count: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlossaryEntry {
    pub id: Option<i64>,
    pub source_term: String,
    pub target_term: String,
    pub notes: Option<String>,
    pub character_name: Option<String>,
    pub created_at: String,
}

pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn new<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        
        // Create tables if they don't exist
        conn.execute(
            "CREATE TABLE IF NOT EXISTS translation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                context TEXT,
                created_at TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0
            )",
            [],
        )?;
        
        conn.execute(
            "CREATE TABLE IF NOT EXISTS glossary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_term TEXT NOT NULL,
                target_term TEXT NOT NULL,
                notes TEXT,
                character_name TEXT,
                created_at TEXT NOT NULL
            )",
            [],
        )?;
        
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_source_text ON translation_memory(source_text)",
            [],
        )?;
        
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_glossary_source ON glossary(source_term)",
            [],
        )?;
        
        Ok(Database { conn })
    }
    
    pub fn in_memory() -> Result<Self> {
        let conn = Connection::open_in_memory()?;
        
        // Create tables
        conn.execute(
            "CREATE TABLE IF NOT EXISTS translation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                context TEXT,
                created_at TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0
            )",
            [],
        )?;
        
        conn.execute(
            "CREATE TABLE IF NOT EXISTS glossary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_term TEXT NOT NULL,
                target_term TEXT NOT NULL,
                notes TEXT,
                character_name TEXT,
                created_at TEXT NOT NULL
            )",
            [],
        )?;
        
        Ok(Database { conn })
    }
    
    pub fn add_translation(&self, entry: &TranslationMemoryEntry) -> Result<i64> {
        self.conn.execute(
            "INSERT INTO translation_memory (source_text, translated_text, source_lang, target_lang, context, created_at, usage_count)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            [
                &entry.source_text,
                &entry.translated_text,
                &entry.source_lang,
                &entry.target_lang,
                &entry.context.as_deref().unwrap_or(""),
                &entry.created_at,
                &entry.usage_count,
            ],
        )?;
        
        Ok(self.conn.last_insert_rowid())
    }
    
    pub fn find_translation(
        &self,
        source_text: &str,
        source_lang: &str,
        target_lang: &str,
    ) -> Result<Option<TranslationMemoryEntry>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, source_text, translated_text, source_lang, target_lang, context, created_at, usage_count
             FROM translation_memory
             WHERE source_text = ?1 AND source_lang = ?2 AND target_lang = ?3",
        )?;
        
        let mut rows = stmt.query([source_text, source_lang, target_lang])?;
        
        if let Some(row) = rows.next()? {
            Ok(Some(TranslationMemoryEntry {
                id: Some(row.get(0)?),
                source_text: row.get(1)?,
                translated_text: row.get(2)?,
                source_lang: row.get(3)?,
                target_lang: row.get(4)?,
                context: row.get(5)?,
                created_at: row.get(6)?,
                usage_count: row.get(7)?,
            }))
        } else {
            Ok(None)
        }
    }
    
    pub fn add_glossary_entry(&self, entry: &GlossaryEntry) -> Result<i64> {
        self.conn.execute(
            "INSERT INTO glossary (source_term, target_term, notes, character_name, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            [
                &entry.source_term,
                &entry.target_term,
                &entry.notes.as_deref().unwrap_or(""),
                &entry.character_name.as_deref().unwrap_or(""),
                &entry.created_at,
            ],
        )?;
        
        Ok(self.conn.last_insert_rowid())
    }
    
    pub fn get_all_glossary(&self) -> Result<Vec<GlossaryEntry>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, source_term, target_term, notes, character_name, created_at FROM glossary",
        )?;
        
        let rows = stmt.query_map([], |row| {
            Ok(GlossaryEntry {
                id: Some(row.get(0)?),
                source_term: row.get(1)?,
                target_term: row.get(2)?,
                notes: row.get(3)?,
                character_name: row.get(4)?,
                created_at: row.get(5)?,
            })
        })?;
        
        let mut entries = Vec::new();
        for row in rows {
            entries.push(row?);
        }
        
        Ok(entries)
    }
    
    pub fn increment_usage(&self, id: i64) -> Result<()> {
        self.conn.execute(
            "UPDATE translation_memory SET usage_count = usage_count + 1 WHERE id = ?1",
            [id],
        )?;
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_database_operations() {
        let db = Database::in_memory().unwrap();
        
        let entry = TranslationMemoryEntry {
            id: None,
            source_text: "こんにちは".to_string(),
            translated_text: "Hello".to_string(),
            source_lang: "ja".to_string(),
            target_lang: "en".to_string(),
            context: None,
            created_at: "2024-01-01T00:00:00Z".to_string(),
            usage_count: 0,
        };
        
        let id = db.add_translation(&entry).unwrap();
        assert!(id > 0);
        
        let found = db
            .find_translation("こんにちは", "ja", "en")
            .unwrap()
            .unwrap();
        
        assert_eq!(found.translated_text, "Hello");
    }
}
