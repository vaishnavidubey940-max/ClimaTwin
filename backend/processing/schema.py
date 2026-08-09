"""Safe mapping from common raw-data labels to the internal climate schema."""

from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd


CORE_FIELDS = ("timestamp", "latitude", "longitude")
CLIMATE_FIELDS = (
    "temperature",
    "min_temperature",
    "max_temperature",
    "rainfall",
    "humidity",
    "pressure",
    "wind_speed",
    "cloud_cover",
)
IDENTITY_FIELDS = ("station_id", "location_name")

# Exact normalized labels only. Ambiguous source fields are deliberately absent.
FIELD_ALIASES = {
    "timestamp": {"timestamp", "datetime", "date_time", "date", "time", "observation_time"},
    "latitude": {"latitude", "lat", "y"},
    "longitude": {"longitude", "lon", "lng", "long", "x"},
    "temperature": {"temperature", "temp", "temp_c", "temperature_c"},
    "min_temperature": {"min_temperature", "min_temp", "tmin"},
    "max_temperature": {"max_temperature", "max_temp", "tmax"},
    "rainfall": {"rainfall", "rainfall_mm", "rain_mm", "precipitation_mm"},
    "humidity": {"humidity", "relative_humidity", "rh"},
    "pressure": {"pressure", "surface_pressure"},
    "wind_speed": {"wind_speed", "windspeed"},
    "cloud_cover": {"cloud_cover", "cloudcover"},
    "station_id": {"station_id", "station", "station_code"},
    "location_name": {"location_name", "location", "place", "city", "district"},
}


def normalize_column_name(name: str) -> str:
    """Turn a raw label into a comparison key without guessing its meaning."""
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


@dataclass(frozen=True)
class SchemaMappingResult:
    """Mapped dataframe and an audit-friendly summary of mapping decisions."""

    dataframe: pd.DataFrame
    mapping: dict[str, str]
    unmapped_columns: list[str]
    ambiguous_columns: dict[str, list[str]]

    def report(self) -> dict[str, object]:
        return {
            "mapped_columns": self.mapping,
            "unmapped_columns": self.unmapped_columns,
            "ambiguous_columns": self.ambiguous_columns,
        }


def map_schema(dataframe: pd.DataFrame) -> SchemaMappingResult:
    """Map known column labels while retaining unrecognized data unchanged."""
    normalized_aliases = {
        field: {normalize_column_name(alias) for alias in aliases}
        for field, aliases in FIELD_ALIASES.items()
    }
    candidates: dict[str, list[str]] = {field: [] for field in FIELD_ALIASES}
    unmatched: list[str] = []

    for column in dataframe.columns:
        matched_fields = [
            field for field, aliases in normalized_aliases.items()
            if normalize_column_name(str(column)) in aliases
        ]
        if len(matched_fields) == 1:
            candidates[matched_fields[0]].append(str(column))
        else:
            unmatched.append(str(column))

    mapping: dict[str, str] = {}
    ambiguous: dict[str, list[str]] = {}
    for field, columns in candidates.items():
        if len(columns) == 1:
            mapping[columns[0]] = field
        elif len(columns) > 1:
            # Choosing between two plausible raw measurements would be unsafe.
            ambiguous[field] = columns

    mapped_sources = set(mapping)
    unmapped = sorted(set(unmatched + [
        column for columns in ambiguous.values() for column in columns
    ]))
    result = dataframe.rename(columns=mapping).copy()
    return SchemaMappingResult(result, mapping, unmapped, ambiguous)
