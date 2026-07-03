#!/usr/bin/env python3
"""Aggregate SPPG data by province and city/regency."""

import json
from collections import defaultdict
from pathlib import Path


def aggregate_sppg(data):
    """Aggregate SPPG data by province and city/regency."""
    # Nested dict: province -> city -> count
    aggregated = defaultdict(lambda: defaultdict(int))

    for item in data:
        province = item.get("provinsi", "UNKNOWN")
        city = item.get("kab_kota", "UNKNOWN")
        aggregated[province][city] += 1

    return aggregated


def main():
    # Read the JSON file
    input_file = Path(__file__).parent / "output" / "sppg_data.json"
    with open(input_file, "r") as f:
        data = json.load(f)

    # Aggregate
    aggregated = aggregate_sppg(data)

    # Sort by province, then by city
    sorted_provinces = sorted(aggregated.keys())

    # Output as JSON
    output = []
    for province in sorted_provinces:
        cities = aggregated[province]
        sorted_cities = sorted(cities.keys())
        for city in sorted_cities:
            output.append({
                "PROVINCE": province,
                "CITY_REGENCY": city,
                "COUNT": cities[city]
            })

    output_file = Path(__file__).parent / "output" / "sppg_aggregated.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    # Print to console
    print(f"{'PROVINCE':<30} {'CITY/REGENCY':<30} {'COUNT':<10}")
    print("=" * 70)
    total_count = 0
    for item in output:
        print(f"{item['PROVINCE']:<30} {item['CITY_REGENCY']:<30} {item['COUNT']:<10}")
        total_count += item['COUNT']
    print("=" * 70)
    print(f"Total: {total_count} SPPG locations across {len(output)} cities/regencies")

    # Also create a province-level summary
    province_summary = []
    for province in sorted_provinces:
        cities = aggregated[province]
        total = sum(cities.values())
        province_summary.append({
            "PROVINCE": province,
            "CITY_COUNT": len(cities),
            "SPPG_COUNT": total
        })

    province_file = Path(__file__).parent / "output" / "sppg_by_province.json"
    with open(province_file, "w") as f:
        json.dump(province_summary, f, indent=2)

    print(f"\nSaved detailed output to: {output_file}")
    print(f"Saved province summary to: {province_file}")


if __name__ == "__main__":
    main()
