/// Error hierarchy mirroring the original exit-code contract:
/// data problems → exit 1, generation problems → exit 2.
#[derive(Debug, thiserror::Error)]
pub enum Error {
    /// YAML syntax error, empty file or non-mapping document.
    #[error("{0}")]
    YamlParse(String),
    /// Schema validation error (missing / invalid field).
    #[error("{0}")]
    Validation(String),
    /// Card key referenced by a deck is not in the data store.
    #[error("{0}")]
    CardNotFound(String),
    /// PDF composition or output failure.
    #[error("{0}")]
    Generation(String),
}

impl Error {
    pub fn exit_code(&self) -> i32 {
        match self {
            Error::YamlParse(_) | Error::Validation(_) | Error::CardNotFound(_) => 1,
            Error::Generation(_) => 2,
        }
    }
}

pub type Result<T> = std::result::Result<T, Error>;
