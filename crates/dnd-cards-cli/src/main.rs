//! `dnd-cards` — generate print-ready PDF reference cards for DnD 5.5e.

use std::path::{Path, PathBuf};
use std::process::ExitCode;

use clap::{Parser, Subcommand};
use dnd_cards_core::layout::BODY_SIZE;
use dnd_cards_core::{
    config, layout_info, load_deck, printed_count, resolve_deck, scan_cards, CardData, Error,
    LayoutInfo,
};

#[derive(Parser)]
#[command(
    name = "dnd-cards",
    version,
    about = "Generate print-ready PDF reference cards for DnD 5.5e."
)]
struct Cli {
    /// Card data directory (default: $DND_CARDS_DATA, ./data, or data/ next to the binary).
    #[arg(long, global = true)]
    data_dir: Option<PathBuf>,

    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Generate a print-ready PDF from a deck profile.
    Generate {
        /// Path to deck profile YAML file.
        #[arg(long)]
        deck: PathBuf,
        /// Output directory for the generated PDF.
        #[arg(long, default_value = "output")]
        output_dir: PathBuf,
        /// Duplex-ready PDF: fronts and backs on separate pages.
        #[arg(long)]
        duplex: bool,
        /// Print cards in deck order instead of sorting by type, level and name.
        #[arg(long)]
        deck_order: bool,
    },
    /// Validate a deck profile and all referenced cards without generating a PDF.
    Validate {
        #[arg(long)]
        deck: PathBuf,
        /// List every card that uses the back face, smaller text or extra cards.
        #[arg(long)]
        layout: bool,
    },
    /// List available cards in the data store.
    List {
        /// Filter by card type (directory name, e.g. `spells`).
        #[arg(long = "type")]
        card_type: Option<String>,
    },
}

fn data_dir(cli: &Option<PathBuf>) -> PathBuf {
    cli.clone()
        .or_else(config::find_data_dir)
        .unwrap_or_else(|| PathBuf::from("data"))
}

/// Cards in deck order, each distinct card once.
fn unique(cards: &[CardData]) -> Vec<&CardData> {
    let mut seen = std::collections::HashSet::new();
    cards
        .iter()
        .filter(|c| seen.insert((&c.card_type, &c.id)))
        .collect()
}

fn describe(info: &LayoutInfo) -> String {
    let mut parts = vec![format!("{}pt", info.font_size)];
    if info.uses_back {
        parts.push("continues on the back".into());
    }
    if info.cards > 1 {
        parts.push(format!("{} cards", info.cards));
    }
    parts.join(", ")
}

fn run(cli: Cli) -> Result<(), Error> {
    let data = data_dir(&cli.data_dir);
    match cli.command {
        Command::Generate {
            deck,
            output_dir,
            duplex,
            deck_order,
        } => {
            let profile = load_deck(&deck)?;
            let mut cards =
                resolve_deck(&profile, &scan_cards(&data), &deck.display().to_string())?;
            if !deck_order {
                dnd_cards_core::sort_cards(&mut cards);
            }
            for c in unique(&cards) {
                let info = layout_info(c);
                if info.cards > 1 {
                    eprintln!("note: {} is printed on {} cards", c.name, info.cards);
                }
            }
            let stem = deck
                .file_stem()
                .map(|s| s.to_string_lossy().into_owned())
                .unwrap_or_else(|| "deck".into());
            let out = output_dir.join(format!("{stem}.pdf"));
            dnd_cards_core::write_pdf(&cards, &out, duplex)?;
            println!("{}", out.display());
        }
        Command::Validate { deck, layout } => {
            let profile = load_deck(&deck)?;
            let cards = resolve_deck(&profile, &scan_cards(&data), &deck.display().to_string())?;
            let (mut back, mut small, mut multi) = (0, 0, 0);
            for c in unique(&cards) {
                let info = layout_info(c);
                back += usize::from(info.uses_back);
                small += usize::from(info.font_size < BODY_SIZE);
                multi += usize::from(info.cards > 1);
                if layout && !info.is_default() {
                    println!("  {}: {}", c.name, describe(&info));
                }
            }
            println!(
                "{}: OK ({} cards, {} printed; {back} continue on the back, {small} with smaller text, {multi} on several cards)",
                deck.display(),
                cards.len(),
                printed_count(&cards),
            );
        }
        Command::List { card_type } => {
            if !Path::new(&data).is_dir() {
                return Ok(());
            }
            let mut entries: Vec<(String, String)> = scan_cards(&data)
                .into_values()
                .filter(|r| card_type.as_ref().is_none_or(|t| &r.card_type == t))
                .map(|r| {
                    (
                        r.path.file_stem().unwrap().to_string_lossy().into_owned(),
                        r.card_type,
                    )
                })
                .collect();
            entries.sort();
            for (stem, t) in entries {
                println!("{stem} [{t}]");
            }
        }
    }
    Ok(())
}

fn main() -> ExitCode {
    match run(Cli::parse()) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            ExitCode::from(e.exit_code() as u8)
        }
    }
}
