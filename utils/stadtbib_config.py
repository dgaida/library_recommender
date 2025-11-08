#!/usr/bin/env python3
"""Stadtteilbibliotheken-Konfiguration"""

# Mapping: Vollständiger Name -> Abkürzung
STADTTEILBIBLIOTHEKEN = {
    "stadtteilbibliothek bocklemünd-mengenich": "BM",
    "stadtteilbibliothek chorweiler": "CW",
    "stadtteilbibliothek ehrenfeld": "EF",
    "stadtteilbibliothek haus balchem": "HB",
    "stadtteilbibliothek kalk": "KK",
    "stadtteilbibliothek mülheim": "MH",
    "stadtteilbibliothek neubrück": "NB",
    "stadtteilbibliothek nippes": "NI",
    "stadtteilbibliothek porz": "PO",
    "stadtteilbibliothek rodenkirchen": "RO",
    "stadtteilbibliothek sülz": "SZ",
}


def get_stadtbib_abbreviation(location_name: str) -> str:
    """
    Gibt Abkürzung für Stadtteilbibliothek zurück.

    Args:
        location_name: Name der Stadtteilbibliothek (normalisiert)

    Returns:
        Abkürzung oder Original-Name
    """
    location_lower = location_name.lower().strip()
    return STADTTEILBIBLIOTHEKEN.get(location_lower, location_name)
