"""Elevation and flood exposure calculation engine for Kerala property plots.

Uses the Google Elevation and Geocoding APIs (needs GOOGLE_MAPS_API_KEY). The river
basin zones and the longitude-based elevation estimate are demo data, loaded only
from `tests/fixtures/` in demo mode (`KANDEZ_FIXTURES`).
"""

from __future__ import annotations

import json
import math
import os
import urllib.parse
import urllib.request
from typing import Any

from app import fixtures
from app.domain.models import ElevationFloodResult, FloodRiskLevel


class ElevationUnavailableError(RuntimeError):
    """Raised when no elevation source is available (no API key, not in demo mode)."""


def _hydrological_zones() -> list[dict[str, Any]]:
    return fixtures.load("hydrological_zones", [])


class ElevationFloodCalculator:
    """Calculates plot elevation above MSL and computes multi-factor flood exposure."""

    def __init__(self, api_key: str | None = None):
        self.api_key = (
            api_key
            or os.environ.get("GOOGLE_MAPS_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("VITE_GOOGLE_MAPS_API_KEY")
            or ""
        )

    def calculate(
        self,
        latitude: float,
        longitude: float,
        locality_hint: str | None = None,
        plot_extent_cents: float | None = None,
    ) -> ElevationFloodResult:
        """Calculates plot elevation and flood exposure risk."""
        elevation_m, resolution_m = self._fetch_elevation(latitude, longitude)
        locality_name, district, taluk = self._resolve_location(latitude, longitude, locality_hint)
        matched_zone = self._find_nearest_hydrological_zone(latitude, longitude)

        if resolution_m is None and matched_zone:
            dist_km = self._haversine_distance(latitude, longitude, matched_zone["lat"], matched_zone["lng"])
            if dist_km <= matched_zone["radius_km"]:
                weight = max(0.0, 1.0 - (dist_km / matched_zone["radius_km"]))
                elevation_m = round((matched_zone["typical_msl"] * weight) + (elevation_m * (1.0 - weight)), 1)

        river_basin = matched_zone["basin"] if matched_zone else "Local Watershed"
        inundation_2018 = matched_zone["inundation_2018"] if (matched_zone and elevation_m < 12.0) else False

        risk_level, risk_score = self._compute_flood_risk(elevation_m, inundation_2018, matched_zone)
        advisory = self._generate_ksdma_advisory(elevation_m, risk_level, matched_zone)
        wetland_risk = self._evaluate_wetland_topography(elevation_m, risk_level)
        plinth_m = self._calculate_recommended_plinth(elevation_m, risk_level)
        checklist = self._build_physical_checklist(elevation_m, risk_level, matched_zone)
        whatsapp_msg = self._draft_malayalam_inquiry(locality_name, elevation_m, risk_level, river_basin)
        whatsapp_msg_en = self._draft_english_inquiry(locality_name, elevation_m, risk_level, river_basin)

        return ElevationFloodResult(
            latitude=round(latitude, 5),
            longitude=round(longitude, 5),
            elevation_meters=round(elevation_m, 1),
            resolution_meters=round(resolution_m, 1) if resolution_m is not None else None,
            locality_name=locality_name,
            district=district,
            taluk_or_village=taluk,
            flood_risk_level=risk_level,
            flood_risk_score=risk_score,
            river_basin=river_basin,
            inundation_2018_zone=inundation_2018,
            ksdma_hazard_advisory=advisory,
            wetland_topography_risk=wetland_risk,
            recommended_plinth_height_m=plinth_m,
            physical_inspection_checklist=checklist,
            whatsapp_inquiry_for_seller=whatsapp_msg,
            whatsapp_inquiry_for_seller_en=whatsapp_msg_en,
        )

    def _fetch_elevation(self, lat: float, lng: float) -> tuple[float, float | None]:
        """Queries Google Elevation API; the topographic estimate is used only in demo mode."""
        if self.api_key:
            try:
                url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lng}&key={self.api_key}"
                req = urllib.request.Request(url, headers={"User-Agent": "Kandezhuthu-AI/1.0"})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") == "OK" and data.get("results"):
                        res = data["results"][0]
                        return float(res["elevation"]), float(res.get("resolution", 10.0))
            except Exception:
                pass

        if fixtures.is_demo():
            return self._estimate_kerala_elevation(lat, lng), None
        raise ElevationUnavailableError(
            "Elevation needs GOOGLE_MAPS_API_KEY (Google Elevation API) or a successful API response."
        )

    def _estimate_kerala_elevation(self, lat: float, lng: float) -> float:
        """Topographic calculation of Kerala elevation based on longitude gradient and river basins."""
        coast_lng = 76.05
        ghats_lng = 77.15
        progress = max(0.0, min(1.0, (lng - coast_lng) / (ghats_lng - coast_lng)))

        if progress < 0.25:
            elev = 1.2 + (progress / 0.25) * 5.0
        elif progress < 0.55:
            p_mid = (progress - 0.25) / 0.30
            elev = 6.2 + (p_mid**1.4) * 50.0
        else:
            p_high = (progress - 0.55) / 0.45
            elev = 56.2 + (p_high**2.0) * 450.0

        return round(max(0.5, elev), 1)

    def _resolve_location(
        self, lat: float, lng: float, hint: str | None
    ) -> tuple[str, str, str | None]:
        """Resolves locality and district via Google Geocoding or closest Kerala landmark."""
        if self.api_key:
            try:
                url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={self.api_key}"
                req = urllib.request.Request(url, headers={"User-Agent": "Kandezhuthu-AI/1.0"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") == "OK" and data.get("results"):
                        result = data["results"][0]
                        locality = None
                        district = "Kerala"
                        taluk = None
                        for comp in result.get("address_components", []):
                            types = comp.get("types", [])
                            if "locality" in types or "sublocality_level_1" in types:
                                locality = comp.get("long_name")
                            if "administrative_area_level_2" in types:
                                district = comp.get("long_name")
                            if "administrative_area_level_3" in types:
                                taluk = comp.get("long_name")
                        if locality:
                            return locality, district, taluk
            except Exception:
                pass

        if hint:
            parts = [p.strip() for p in hint.split(",")]
            loc = parts[0]
            dist = parts[1] if len(parts) > 1 else "Kerala"
            return loc, dist, None

        nearest = self._find_nearest_hydrological_zone(lat, lng)
        if nearest:
            return nearest["name"].split(" - ")[0], nearest["district"], nearest["name"]

        return f"Plot ({lat:.4f}, {lng:.4f})", "Kerala", None

    def _find_nearest_hydrological_zone(self, lat: float, lng: float) -> dict[str, Any] | None:
        closest_zone = None
        min_dist = float("inf")

        for zone in _hydrological_zones():
            d = self._haversine_distance(lat, lng, zone["lat"], zone["lng"])
            if d <= zone["radius_km"] and d < min_dist:
                min_dist = d
                closest_zone = zone

        return closest_zone

    def _compute_flood_risk(
        self, elevation_m: float, inundation_2018: bool, zone: dict[str, Any] | None
    ) -> tuple[FloodRiskLevel, int]:
        if elevation_m < 2.0:
            risk = FloodRiskLevel.CRITICAL
            score = max(5, int(elevation_m * 15))
        elif elevation_m < 5.0:
            if inundation_2018 or (zone and zone["inundation_2018"]):
                risk = FloodRiskLevel.HIGH
                score = 30 + int(elevation_m * 4)
            else:
                risk = FloodRiskLevel.MODERATE
                score = 45 + int(elevation_m * 4)
        elif elevation_m < 12.0:
            if inundation_2018:
                risk = FloodRiskLevel.MODERATE
                score = 60 + int((elevation_m - 5.0) * 3)
            else:
                risk = FloodRiskLevel.LOW
                score = 75 + int((elevation_m - 5.0) * 2)
        else:
            risk = FloodRiskLevel.LOW
            score = min(98, 85 + int((elevation_m - 12.0) * 0.5))

        return risk, score

    def _generate_ksdma_advisory(
        self, elevation_m: float, risk: FloodRiskLevel, zone: dict[str, Any] | None
    ) -> str:
        if zone and zone.get("advisory"):
            return zone["advisory"]

        if risk == FloodRiskLevel.CRITICAL:
            return (
                f"KSDMA Hazard Zone Alert: Elevation is only {elevation_m}m above Mean Sea Level. "
                "High water table and severe tidal/monsoonal waterlogging susceptibility. "
                "Mandatory stilt construction or minimum 1.5m plinth elevation required by local authorities."
            )
        if risk == FloodRiskLevel.HIGH:
            return (
                f"KSDMA Riparian Alert: Plot at {elevation_m}m MSL is situated in a low-lying valley or river basin. "
                "Ensure building plinth is elevated at least 1.0m to 1.2m above the crown of the access road."
            )
        if risk == FloodRiskLevel.MODERATE:
            return (
                f"KSDMA Moderate Drainage Notice: Plot at {elevation_m}m MSL has fair elevation. "
                "Ensure local municipal or panchayat storm water drains have adequate downhill gradient."
            )
        return (
            f"KSDMA Safe Topography: Plot is at an elevated {elevation_m}m MSL. "
            "Safe from river inundation and regional monsoon flooding. Standard KPBR setbacks and plinth apply."
        )

    def _evaluate_wetland_topography(self, elevation_m: float, risk: FloodRiskLevel) -> str:
        if elevation_m < 3.5:
            return (
                "▲ CRITICAL WETLAND RISK: Lands under 3.5m MSL in Kerala are frequently classified in Village BTR "
                "as 'Nilam' (Paddy Land), 'Nanja', or 'Wetland'. Verify the property is NOT listed in the "
                "Krishi Bhavan Agricultural Data Bank under the 2008 Act before paying earnest money."
            )
        if elevation_m < 8.0:
            return (
                "Moderate Topographic Risk: Verify whether the land was reclaimed or converted prior to 2008. "
                "If revenue records show 'Nilam', Form 6 Section 27A fee regularisation may be required."
            )
        return "Dry Land Profile: Natural midland/upland elevation consistent with 'Purayidam' (Garden Land / Dry Land)."

    def _calculate_recommended_plinth(self, elevation_m: float, risk: FloodRiskLevel) -> float:
        if risk == FloodRiskLevel.CRITICAL:
            return 1.5
        if risk == FloodRiskLevel.HIGH:
            return 1.1
        if risk == FloodRiskLevel.MODERATE:
            return 0.75
        return 0.6

    def _build_physical_checklist(
        self, elevation_m: float, risk: FloodRiskLevel, zone: dict[str, Any] | None
    ) -> list[str]:
        items = [
            f"Verify that the plot surface is not recessed below the crown of the access road (current MSL: ~{elevation_m}m).",
            "Examine adjacent compound walls, bridge pillars, and electric posts for 2018/monsoon flood watermark lines.",
            "Inspect neighborhood storm water drainage: check if Panchayat culverts have unobstructed gravity flow.",
            "Inquire with senior local neighbors (കുറേക്കാലമായി താമസിക്കുന്നവർ) regarding monsoon waterlogging during July-August.",
        ]
        if risk in (FloodRiskLevel.CRITICAL, FloodRiskLevel.HIGH):
            items.insert(
                0,
                "Inspect soil bearing capacity with a geotechnical core test before finalizing foundation design (pile vs spread footing).",
            )
        return items

    def _draft_malayalam_inquiry(
        self, locality: str, elevation_m: float, risk: FloodRiskLevel, basin: str
    ) -> str:
        return (
            f"നമസ്കാരം, {locality} പ്രദേശത്തെ പ്രോപ്പർട്ടിയുടെ ലൊക്കേഷനും ഉയരവും ({elevation_m}m MSL - {basin}) "
            "പരിശോധിച്ചതിൽ മഴക്കാലത്തെ വെള്ളപ്പൊക്ക സാധ്യതയെക്കുറിച്ച് (Flood & Waterlogging) താഴെ പറയുന്ന കാര്യങ്ങളിൽ വ്യക്തത തേടുന്നു:\n"
            "1. 2018-ലോ 2019-ലോ ഉണ്ടായ മഹാപ്രളയത്തിൽ ഈ പ്ലോട്ടിലോ പ്രവേശിക്കുന്ന റോഡിലോ വെള്ളം കയറിയിരുന്നോ? പരമാവധി എത്ര അടി ഉയരത്തിൽ വെള്ളം വന്നിരുന്നു?\n"
            "2. കനത്ത മഴയുള്ള സമയത്ത് പ്ലോട്ടിലോ ചുറ്റുവട്ടത്തോ വെള്ളക്കെട്ട് (water stagnation) ഉണ്ടാകാറുണ്ടോ? വെള്ളം ഒഴുകിപ്പോകാൻ പഞ്ചായത്ത്/മുനിസിപ്പാലിറ്റി കാന സൗകര്യമുണ്ടോ?\n"
            "3. വീട് നിർമ്മിക്കുമ്പോൾ റോഡ് നിരപ്പിൽ നിന്നും പ്ലിന്ത് ലെവൽ (Plinth Level) എത്ര ഉയരത്തിൽ പണിയേണ്ടി വരും? സമീപത്തെ വീടുകൾ ഉയർന്ന തറയിലാണോ നിർമ്മിച്ചിട്ടുള്ളത്?\n"
            "ഈ വിവരങ്ങൾ ലഭ്യമാക്കിയാൽ വലിയ ഉപകാരമായിരിക്കും. നന്ദി."
        )

    def _draft_english_inquiry(
        self, locality: str, elevation_m: float, risk: FloodRiskLevel, basin: str
    ) -> str:
        return (
            f"Hello, upon checking the location and elevation of the property in {locality} ({elevation_m}m MSL - {basin}), "
            "we would appreciate clarification on the monsoon flood history and drainage conditions:\n"
            "1. Did flood waters enter this plot or the access road during the 2018 or 2019 Kerala floods? If so, what was the approximate water level?\n"
            "2. Does the plot or surrounding area experience waterlogging or stagnation during heavy monsoon rains? Are municipal/panchayat stormwater drains functional?\n"
            "3. What is the required plinth level height relative to the road for residential construction in this area?\n"
            "Thank you for your assistance."
        )

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c
