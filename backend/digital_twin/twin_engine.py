"""Central Digital Twin coordinator."""

import json
from datetime import datetime, timezone

from backend.digital_twin.snapshot import serialize
from backend.digital_twin.state_builder import StateBuilder
from backend.data_sources.data_manager import DataManager

class TwinEngine:
    def __init__(self, repository, config: dict):
        self.repository = repository
        self.config = config
        self.data_mode = config.get("DATA_MODE", "LOCAL")
        self.builder = StateBuilder(repository, self.data_mode)
        self.data_manager = DataManager(config)

    def _fetch_live_data_if_needed(self, location_id: int):
        location = next((x for x in self.repository.twin_locations() if x["id"] == location_id), None)
        if not location:
            return

        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is None or lon is None:
            return

        latest = self.repository.get_latest_observation(location_id)
        needs_fetch = True
        
        if latest and latest.get("timestamp"):
            try:
                obs_time = datetime.fromisoformat(latest["timestamp"].replace("Z", "+00:00"))
                if obs_time.tzinfo is None:
                    obs_time = obs_time.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - obs_time).total_seconds() / 3600
                if age_hours < 1.0:
                    needs_fetch = False
            except ValueError:
                pass

        if needs_fetch:
            try:
                meteo_data = self.data_manager.imd.fetch_latest_data(latitude=lat, longitude=lon)
                nasa_data = self.data_manager.mosdac.fetch_latest_data(latitude=lat, longitude=lon)
                
                if meteo_data:
                    obs = {
                        "location_id": location_id,
                        "timestamp": meteo_data["timestamp"],
                        "source": "open-meteo",
                        "source_dataset": "open-meteo-forecast",
                        "original_file": "live-api",
                        "station_id": None,
                        "ingested_at": datetime.now(timezone.utc).isoformat(),
                        "observation_key": f"{location_id}-{meteo_data['timestamp']}"
                    }
                    obs.update(meteo_data["measurements"])
                    
                    if nasa_data:
                        obs["original_file"] = f"live-api | nasa-cmr-granule:{nasa_data.get('granule_id')}"
                        
                    self.repository.insert_observation(obs)
                    self.repository.connection.commit()
            except Exception as e:
                print(f"Dynamic fetch error: {e}")

    def get_twin(self, location_id: int):
        self._fetch_live_data_if_needed(location_id)
        state = self.builder.build(location_id)
        return state.to_dict()

    def update_twin(self, location_id: int):
        self._fetch_live_data_if_needed(location_id)
        state = self.builder.build(location_id)
        snapshot = serialize(state)
        self.repository.save_twin_snapshot(
            location_id, 
            state.generated_at, 
            (state.observed_state or {}).get("timestamp"), 
            snapshot, 
            self.data_mode, 
            state.quality["status"]
        )
        self.repository.connection.commit()
        return snapshot

    def get_all_twin_statuses(self): 
        return [
            {"location": location, "twin_id": f"climatwin-location-{location['id']}", "snapshot": self.repository.latest_twin_snapshot(location["id"])} 
            for location in self.repository.twin_locations()
        ]
