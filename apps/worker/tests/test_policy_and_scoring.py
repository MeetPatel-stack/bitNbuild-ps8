from datetime import datetime, timezone, timedelta
from app.schemas.flight import FlightOption
from app.schemas.policy import DisruptionPolicy
from app.policies.policy_engine import policy_engine
from app.policies.scoring_engine import scoring_engine


def test_policy_filtering_and_option_parsing():
    now = datetime.now(timezone.utc)
    policy = DisruptionPolicy(
        max_extra_fare=5000.0,
        max_stops=1,
        cabin_required="Economy",
    )

    opt_valid = FlightOption(
        option_id="opt-valid-1",
        airline="Air India",
        flight_number="AI-403",
        origin="AMD",
        destination="LHR",
        departure=now + timedelta(hours=3),
        arrival=now + timedelta(hours=14),
        stops=1,
        fare=30000.0,
        extra_fare=0.0,
        cabin="Economy",
    )

    opt_high_fare = FlightOption(
        option_id="opt-high-fare",
        airline="Emirates",
        flight_number="EK-500",
        origin="AMD",
        destination="LHR",
        departure=now + timedelta(hours=4),
        arrival=now + timedelta(hours=15),
        stops=1,
        fare=45000.0,
        extra_fare=12000.0,  # Exceeds max 5000
        cabin="Economy",
    )

    opt_too_many_stops = FlightOption(
        option_id="opt-too-many-stops",
        airline="Multiple",
        flight_number="M-101",
        origin="AMD",
        destination="LHR",
        departure=now + timedelta(hours=5),
        arrival=now + timedelta(hours=22),
        stops=2,  # Exceeds max 1
        fare=28000.0,
        extra_fare=0.0,
        cabin="Economy",
    )

    opt_biz_cabin = FlightOption(
        option_id="opt-biz",
        airline="British Airways",
        flight_number="BA-100",
        origin="AMD",
        destination="LHR",
        departure=now + timedelta(hours=6),
        arrival=now + timedelta(hours=16),
        stops=1,
        fare=80000.0,
        extra_fare=4000.0,
        cabin="Business",  # Mismatch with Economy
    )

    options = [opt_valid, opt_high_fare, opt_too_many_stops, opt_biz_cabin]
    valid_opts, eval_res = policy_engine.filter_options(options, policy)

    assert len(valid_opts) == 1
    assert valid_opts[0].option_id == "opt-valid-1"
    assert eval_res.total_options_evaluated == 4
    assert eval_res.valid_options_count == 1


def test_scoring_engine_selection_and_explanation():
    now = datetime.now(timezone.utc)
    opt1 = FlightOption(
        option_id="opt-1",
        airline="Air India",
        flight_number="AI-403",
        origin="AMD",
        destination="LHR",
        departure=now + timedelta(hours=3),
        arrival=now + timedelta(hours=14),
        stops=1,
        fare=30000.0,
        extra_fare=0.0,
        cabin="Economy",
        available_seats=6,
    )

    opt2 = FlightOption(
        option_id="opt-2",
        airline="IndiGo",
        flight_number="6E-901",
        origin="AMD",
        destination="LHR",
        departure=now + timedelta(hours=4),
        arrival=now + timedelta(hours=18),
        stops=1,
        fare=34000.0,
        extra_fare=4000.0,
        cabin="Economy",
        available_seats=2,
    )

    best_opt, reason, scored = scoring_engine.select_best_option([opt1, opt2])

    assert best_opt is not None
    assert best_opt.option_id == "opt-1"
    assert "Score" in reason
    assert len(scored) == 2
    assert scored[0]["score"] > scored[1]["score"]


def test_no_valid_alternatives_scenario():
    now = datetime.now(timezone.utc)
    policy = DisruptionPolicy(max_extra_fare=500.0, max_stops=0)

    # Option has 1 stop and extra fare 2000
    expensive_opt = FlightOption(
        option_id="opt-exp",
        airline="Airline",
        flight_number="XX-1",
        origin="AMD",
        destination="LHR",
        departure=now,
        arrival=now + timedelta(hours=10),
        stops=1,
        extra_fare=2000.0,
        cabin="Economy",
    )

    valid_opts, eval_res = policy_engine.filter_options([expensive_opt], policy)
    assert len(valid_opts) == 0
    assert eval_res.valid_options_count == 0
    assert len(eval_res.evaluations[0].rejection_reasons) == 2
