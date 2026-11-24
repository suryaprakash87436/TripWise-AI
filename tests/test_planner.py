from pathlib import Path
from planner import parse_destination_records, TripPlanner

def test_parse_destination_records():
    records = parse_destination_records(
        "DESTINATION: Test City\nSTATE: Test State\n\nDESTINATION: Other\nSTATE: X"
    )
    assert len(records) == 2
    assert records[0]["DESTINATION"] == "Test City"

def test_retrieve_returns_known_destination():
    planner = TripPlanner(Path(__file__).parents[1] / "data" / "destinations.txt")
    results = planner.retrieve("beach historical family", 10000, 3)
    assert results
    assert all("DESTINATION" in item for _, item, _ in results)
