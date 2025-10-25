#!/usr/bin/env python3
"""
Artist Blacklist System für MP3-Archiv-Analyse

Verwaltet eine Blacklist für Künstler, für die keine CDs in der Bibliothek
gefunden wurden. Jeder Künstler wird maximal einmal pro Jahr überprüft.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
from utils.io import DATA_DIR
from utils.logging_config import get_logger

logger = get_logger(__name__)

ARTIST_BLACKLIST_FILE: str = os.path.join(DATA_DIR, "blacklist_artists.json")
RECHECK_INTERVAL_DAYS: int = 365  # 1 Jahr


class ArtistBlacklist:
    """
    Verwaltet Blacklist für Künstler ohne verfügbare CDs in der Bibliothek.
    
    Ein Künstler kommt auf die Blacklist, wenn:
    - Keine neuen CDs (die nicht bereits in MP3-Sammlung sind) gefunden wurden
    - Die Suche im Bibliothekskatalog durchgeführt wurde
    
    Ein Künstler wird von der Blacklist entfernt, wenn:
    - Das letzte Check-Datum älter als 1 Jahr ist
    - Bei der erneuten Überprüfung neue CDs gefunden werden
    
    Attributes:
        blacklist: Dictionary mit Artist-Name als Key und Metadaten als Value
    """
    
    def __init__(self) -> None:
        """Initialisiert ArtistBlacklist und lädt existierende Daten."""
        self.blacklist: Dict[str, Dict[str, Any]] = self._load_blacklist()
        logger.info(
            f"Artist-Blacklist initialisiert mit {len(self.blacklist)} Einträgen"
        )
    
    def _load_blacklist(self) -> Dict[str, Dict[str, Any]]:
        """
        Lädt die Artist-Blacklist aus der JSON-Datei.
        
        Returns:
            Dictionary mit Artist-Daten
        """
        if os.path.exists(ARTIST_BLACKLIST_FILE):
            try:
                with open(ARTIST_BLACKLIST_FILE, "r", encoding="utf-8") as f:
                    data: Dict[str, Dict[str, Any]] = json.load(f)
                logger.info(
                    f"{len(data)} geblacklistete Künstler aus "
                    f"{ARTIST_BLACKLIST_FILE} geladen"
                )
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.error(
                    f"Fehler beim Laden von {ARTIST_BLACKLIST_FILE}: {e}"
                )
                return {}
        else:
            logger.info("Keine existierende Artist-Blacklist gefunden")
            return {}
    
    def _save_blacklist(self) -> None:
        """Speichert die Artist-Blacklist in die JSON-Datei."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(ARTIST_BLACKLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(self.blacklist, f, ensure_ascii=False, indent=2)
            logger.info(
                f"{len(self.blacklist)} geblacklistete Künstler in "
                f"{ARTIST_BLACKLIST_FILE} gespeichert"
            )
        except IOError as e:
            logger.error(
                f"Fehler beim Speichern von {ARTIST_BLACKLIST_FILE}: {e}"
            )
    
    def is_blacklisted(self, artist_name: str) -> bool:
        """
        Prüft, ob ein Künstler auf der Blacklist steht.
        
        Args:
            artist_name: Name des Künstlers
        
        Returns:
            True wenn geblacklistet und letzter Check < 1 Jahr her, sonst False
        """
        artist_key: str = artist_name.lower().strip()
        
        if artist_key not in self.blacklist:
            return False
        
        # Prüfe, ob Re-Check fällig ist
        last_check_str: str = self.blacklist[artist_key].get("last_checked", "")
        
        try:
            last_check: datetime = datetime.fromisoformat(last_check_str)
            days_since_check: int = (datetime.now() - last_check).days
            
            if days_since_check >= RECHECK_INTERVAL_DAYS:
                logger.info(
                    f"Re-Check fällig für '{artist_name}': "
                    f"{days_since_check} Tage seit letztem Check"
                )
                return False  # Re-Check durchführen
            
            logger.debug(
                f"'{artist_name}' auf Blacklist, "
                f"{days_since_check} Tage seit letztem Check"
            )
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Ungültiges Datum für '{artist_name}': {last_check_str}. "
                f"Fehler: {e}"
            )
            return False  # Bei ungültigem Datum neu checken
    
    def add_to_blacklist(
        self,
        artist_name: str,
        song_count: int,
        reason: str = "Keine neuen CDs in Bibliothek gefunden"
    ) -> None:
        """
        Fügt einen Künstler zur Blacklist hinzu.
        
        Args:
            artist_name: Name des Künstlers
            song_count: Anzahl Songs im MP3-Archiv
            reason: Grund für die Blacklistung
        """
        artist_key: str = artist_name.lower().strip()
        
        if artist_key in self.blacklist:
            logger.debug(f"'{artist_name}' ist bereits geblacklistet")
            # Aktualisiere Datum
            self.blacklist[artist_key]["last_checked"] = datetime.now().isoformat()
            self.blacklist[artist_key]["check_count"] = (
                self.blacklist[artist_key].get("check_count", 1) + 1
            )
        else:
            # Neuer Eintrag
            self.blacklist[artist_key] = {
                "artist_name": artist_name,  # Original-Schreibweise
                "song_count": song_count,
                "reason": reason,
                "added_at": datetime.now().isoformat(),
                "last_checked": datetime.now().isoformat(),
                "check_count": 1,
            }
            logger.info(
                f"✅ '{artist_name}' zur Artist-Blacklist hinzugefügt: {reason}"
            )
        
        self._save_blacklist()
    
    def remove_from_blacklist(self, artist_name: str) -> bool:
        """
        Entfernt einen Künstler von der Blacklist.
        
        Args:
            artist_name: Name des Künstlers
        
        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        artist_key: str = artist_name.lower().strip()
        
        if artist_key in self.blacklist:
            del self.blacklist[artist_key]
            self._save_blacklist()
            logger.info(f"✅ '{artist_name}' von Artist-Blacklist entfernt")
            return True
        
        logger.debug(f"'{artist_name}' nicht auf Blacklist gefunden")
        return False
    
    def get_artists_due_for_recheck(self) -> List[Dict[str, Any]]:
        """
        Gibt alle Künstler zurück, die für einen Re-Check fällig sind.
        
        Returns:
            Liste von Künstler-Dictionaries mit Re-Check-Status
        """
        due_artists: List[Dict[str, Any]] = []
        
        for artist_key, data in self.blacklist.items():
            last_check_str: str = data.get("last_checked", "")
            
            try:
                last_check: datetime = datetime.fromisoformat(last_check_str)
                days_since_check: int = (datetime.now() - last_check).days
                
                if days_since_check >= RECHECK_INTERVAL_DAYS:
                    artist_info: Dict[str, Any] = {
                        "artist_name": data["artist_name"],
                        "days_since_check": days_since_check,
                        "last_checked": last_check_str,
                        "check_count": data.get("check_count", 1),
                        "song_count": data.get("song_count", 0),
                    }
                    due_artists.append(artist_info)
                    
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Ungültiges Datum für '{data.get('artist_name', 'Unknown')}': "
                    f"{last_check_str}"
                )
        
        logger.info(f"{len(due_artists)} Künstler fällig für Re-Check")
        return due_artists
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Artist-Blacklist zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        total_artists: int = len(self.blacklist)
        
        if total_artists == 0:
            return {
                "total_artists": 0,
                "due_for_recheck": 0,
                "recent_additions": 0,
                "most_checked": [],
            }
        
        # Zähle Re-Check fällige Künstler
        due_count: int = len(self.get_artists_due_for_recheck())
        
        # Zähle kürzliche Additions (letzte 30 Tage)
        recent_additions: int = 0
        thirty_days_ago: datetime = datetime.now() - timedelta(days=30)
        
        for data in self.blacklist.values():
            added_at_str: str = data.get("added_at", "")
            try:
                added_at: datetime = datetime.fromisoformat(added_at_str)
                if added_at >= thirty_days_ago:
                    recent_additions += 1
            except (ValueError, TypeError):
                pass
        
        # Top 5 meistgeprüfte Künstler
        most_checked: List[Tuple[str, int]] = sorted(
            [
                (data["artist_name"], data.get("check_count", 1))
                for data in self.blacklist.values()
            ],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        stats: Dict[str, Any] = {
            "total_artists": total_artists,
            "due_for_recheck": due_count,
            "recent_additions": recent_additions,
            "most_checked": most_checked,
        }
        
        return stats
    
    def print_stats(self) -> None:
        """Druckt Statistiken über die Artist-Blacklist."""
        stats: Dict[str, Any] = self.get_stats()
        
        print("\n" + "=" * 60)
        print("ARTIST-BLACKLIST STATISTIKEN")
        print("=" * 60)
        print(f"Gesamt geblacklistete Künstler: {stats['total_artists']}")
        print(f"Fällig für Re-Check: {stats['due_for_recheck']}")
        print(f"Neue Einträge (letzte 30 Tage): {stats['recent_additions']}")
        
        if stats['most_checked']:
            print("\nAm häufigsten geprüft:")
            for artist_name, check_count in stats['most_checked']:
                print(f"  - {artist_name}: {check_count}x geprüft")
        
        print("=" * 60 + "\n")
    
    def clear_old_entries(self, days: int = 730) -> int:
        """
        Entfernt Einträge, die älter als die angegebenen Tage sind.
        
        Args:
            days: Maximales Alter in Tagen (default: 2 Jahre)
        
        Returns:
            Anzahl entfernter Einträge
        """
        cutoff_date: datetime = datetime.now() - timedelta(days=days)
        removed_count: int = 0
        
        artists_to_remove: List[str] = []
        
        for artist_key, data in self.blacklist.items():
            added_at_str: str = data.get("added_at", "")
            
            try:
                added_at: datetime = datetime.fromisoformat(added_at_str)
                if added_at < cutoff_date:
                    artists_to_remove.append(artist_key)
                    
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Ungültiges Datum für '{data.get('artist_name', 'Unknown')}'"
                )
        
        # Entferne alte Einträge
        for artist_key in artists_to_remove:
            artist_name: str = self.blacklist[artist_key]["artist_name"]
            del self.blacklist[artist_key]
            removed_count += 1
            logger.info(f"Alter Eintrag entfernt: '{artist_name}'")
        
        if removed_count > 0:
            self._save_blacklist()
            logger.info(
                f"{removed_count} alte Einträge (>{days} Tage) entfernt"
            )
        
        return removed_count


def get_filtered_top_artists(
    artist_counter: Counter,
    artist_blacklist: ArtistBlacklist,
    top_n: int = 10,
    max_total: int = 20
) -> List[Tuple[str, int]]:
    """
    Gibt die Top N Künstler zurück, die nicht auf der Blacklist stehen.
    
    Durchsucht die Top-Künstler-Liste und überspringt geblacklistete Künstler,
    bis top_n nicht-geblacklistete Künstler gefunden wurden.
    
    Args:
        artist_counter: Counter mit Anzahl Songs pro Künstler
        artist_blacklist: ArtistBlacklist-Instanz
        top_n: Gewünschte Anzahl Top-Künstler
        max_total: Maximale Anzahl zu prüfender Künstler
    
    Returns:
        Liste von (Künstler, Anzahl) Tupeln
    
    Example:
        >>> counter = Counter({"Artist A": 50, "Artist B": 45, "Artist C": 40})
        >>> blacklist = ArtistBlacklist()
        >>> top_artists = get_filtered_top_artists(counter, blacklist, top_n=2)
        >>> print(len(top_artists))
        2
    """
    logger.info(
        f"Filtere Top {top_n} Künstler, "
        f"prüfe maximal {max_total} Kandidaten"
    )
    
    filtered_artists: List[Tuple[str, int]] = []
    checked_count: int = 0
    skipped_count: int = 0
    
    # Iteriere über alle Künstler nach Häufigkeit sortiert
    for artist_name, song_count in artist_counter.most_common(max_total):
        checked_count += 1
        
        # Prüfe ob auf Blacklist
        if artist_blacklist.is_blacklisted(artist_name):
            logger.debug(
                f"Überspringe '{artist_name}' (geblacklistet, "
                f"{song_count} Songs)"
            )
            skipped_count += 1
            continue
        
        # Künstler ist nicht geblacklistet
        filtered_artists.append((artist_name, song_count))
        logger.debug(
            f"Akzeptiert: '{artist_name}' ({song_count} Songs) - "
            f"Position {len(filtered_artists)}"
        )
        
        # Stoppe, wenn genug Künstler gefunden
        if len(filtered_artists) >= top_n:
            break
    
    logger.info(
        f"Gefilterte Top {len(filtered_artists)}: "
        f"{checked_count} geprüft, {skipped_count} übersprungen"
    )
    
    return filtered_artists


def update_artist_blacklist_from_search_results(
    artist_name: str,
    song_count: int,
    found_new_albums: bool,
    artist_blacklist: ArtistBlacklist
) -> None:
    """
    Aktualisiert die Artist-Blacklist basierend auf Suchergebnissen.
    
    Args:
        artist_name: Name des Künstlers
        song_count: Anzahl Songs im MP3-Archiv
        found_new_albums: True wenn neue Alben gefunden wurden
        artist_blacklist: ArtistBlacklist-Instanz
    """
    if found_new_albums:
        # Neue Alben gefunden - von Blacklist entfernen falls vorhanden
        if artist_blacklist.is_blacklisted(artist_name):
            artist_blacklist.remove_from_blacklist(artist_name)
            logger.info(
                f"🎉 '{artist_name}' von Blacklist entfernt - "
                f"neue Alben gefunden!"
            )
    else:
        # Keine neuen Alben - auf Blacklist setzen
        artist_blacklist.add_to_blacklist(
            artist_name,
            song_count,
            reason="Keine neuen CDs in Bibliothek gefunden"
        )
        logger.info(
            f"⚫ '{artist_name}' auf Blacklist gesetzt - "
            f"keine neuen Alben verfügbar"
        )


# Globale Artist-Blacklist-Instanz (Singleton)
_artist_blacklist_instance: Optional[ArtistBlacklist] = None


def get_artist_blacklist() -> ArtistBlacklist:
    """
    Gibt die globale Artist-Blacklist-Instanz zurück (Singleton-Pattern).
    
    Returns:
        Die globale ArtistBlacklist-Instanz
    """
    global _artist_blacklist_instance
    if _artist_blacklist_instance is None:
        _artist_blacklist_instance = ArtistBlacklist()
        logger.info("Neue Artist-Blacklist-Instanz erstellt")
    return _artist_blacklist_instance
