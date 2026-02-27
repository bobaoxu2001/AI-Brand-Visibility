"""Generate and seed 100 highly specific EV prompts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.db import (
    category_breakdown,
    get_connection,
    init_db,
    insert_prompts,
    prompt_count,
    reset_prompt_related_tables,
)


def build_prompt_bank() -> list[tuple[str, str]]:
    prompts_by_category: dict[str, list[str]] = {
        "Budget": [
            "I have a $45,000 all-in budget and commute 70 miles/day in California. Should I buy a used Tesla Model Y, a base Rivian R1T lease takeover, or wait for a discounted Lucid Air Pure?",
            "For a first-time EV buyer in Texas with no home charger and a max payment of $650/month, which is more practical: Tesla Model 3 RWD, Rivian R1S used, or Lucid Air Touring CPO?",
            "If electricity is expensive in my city ($0.31/kWh), which brand gives the lowest 3-year ownership cost: Tesla, Rivian, or Lucid?",
            "I can only spend $8,000 down and need AWD for mountain driving. Which setup is most cost-effective today among Tesla, Rivian, and Lucid options?",
            "I drive 18,000 miles a year for work and care about tire replacement and insurance cost. Which brand tends to be cheapest long-term: Tesla, Rivian, or Lucid?",
            "My HOA does not allow wall charger installation yet. Which brand is most manageable if I rely on public charging 100% of the time?",
            "What is the smartest budget move in 2026: buy a used Tesla now, finance a Lucid Air Pure, or lease a Rivian R1T?",
            "I need an EV under $55k with strong resale in 4 years and enough room for two kids. Which brand is financially safest?",
            "Can you compare total cost for Tesla vs Rivian vs Lucid if I keep the car for only 30 months and then sell?",
            "Which EV brand gives me the best value if my priorities are low depreciation, predictable maintenance, and decent highway range?",
        ],
        "Luxury": [
            "I want a premium EV with a truly quiet cabin at 75 mph and top-tier materials. Is Lucid clearly better than Tesla and Rivian for luxury comfort?",
            "For an executive client shuttle service in Manhattan, which brand feels most premium to passengers: Tesla Model S, Rivian R1S, or Lucid Air Grand Touring?",
            "I care about rear-seat comfort for 2-hour airport rides. Which brand has the best second-row experience: Tesla, Rivian, or Lucid?",
            "Between Tesla Plaid, Lucid Air Sapphire-adjacent trims, and Rivian performance models, which one balances luxury and daily usability best?",
            "Which EV is closest to a Mercedes S-Class interior vibe: Lucid, Tesla, or Rivian?",
            "I regularly host clients and need premium design, subtle status, and smooth ride quality. Which brand is best for professional image?",
            "For a buyer upgrading from a Porsche Taycan, which brand offers the most upscale software + cabin combination?",
            "Which EV brand provides the most luxurious ownership experience including service pickup, loaners, and concierge support?",
            "I dislike minimalist interiors and want tactile controls plus high-end finishes. Which brand aligns best: Rivian, Tesla, or Lucid?",
            "If my top luxury criteria are seat comfort, NVH, and ambient lighting quality, how would you rank Tesla, Rivian, and Lucid?",
        ],
        "Camping": [
            "I do 4-day camping trips in Utah with two e-bikes and rooftop cargo. Which EV brand is better for this lifestyle: Rivian, Tesla, or Lucid?",
            "For dispersed camping without hookups, which model ecosystem is stronger for power outlets, gear storage, and camp setup efficiency?",
            "I need an EV that can handle muddy forest roads on weekends but still commute in the city Monday-Friday. Which brand is the best compromise?",
            "Between Tesla Model X, Rivian R1S, and Lucid Gravity-style alternatives, which is most practical for family camping and long-range road trips?",
            "Which brand has the best real-world cold-weather range while carrying camping equipment and a roof tent?",
            "I want to run a portable fridge and laptop overnight from the car. Which brand supports camp power use most reliably?",
            "I frequently camp 200 miles from major cities. Which charging strategy is safer with Tesla, Rivian, or Lucid?",
            "What should I choose if I prioritize off-road confidence, washable interior, and cargo flexibility for camping gear?",
            "Which EV is better for a surfer-camper routine with wet gear, sandy seats, and frequent highway miles?",
            "For overlanding-lite use (not hardcore rock crawling), should I trust Tesla, Rivian, or Lucid as the better weekend adventure platform?",
        ],
        "Tech": [
            "Which brand currently has the most reliable driver-assistance stack for dense Bay Area traffic: Tesla FSD, Rivian Driver+, or Lucid DreamDrive?",
            "I am a software engineer and want the strongest OTA cadence and feature velocity. Which EV brand moves fastest in useful updates?",
            "For voice controls, route planning intelligence, and charging ETA accuracy, how do Tesla, Rivian, and Lucid compare today?",
            "Which brand offers the most future-proof in-car tech architecture for the next 5 years?",
            "I care about app reliability and remote controls (preconditioning, lock, charge scheduling). Which brand has the best mobile experience?",
            "For someone who hates buggy infotainment, which brand has the most stable day-to-day UI performance?",
            "How do Tesla, Rivian, and Lucid compare on sensor fusion confidence in rain and low-visibility conditions?",
            "I want a tech-forward EV but with minimal phantom braking risk. Which brand is currently strongest?",
            "Which EV brand gives the best integrated navigation + charging + battery preconditioning software stack?",
            "If I prioritize data-rich trip analytics and efficient route optimization, should I choose Tesla, Rivian, or Lucid?",
        ],
        "Family": [
            "I have two toddlers and need easy car-seat loading plus stroller space. Which brand is most family friendly: Tesla, Rivian, or Lucid?",
            "For a five-person household with one grandparent joining often, which EV has the best third-row practicality?",
            "Which brand offers the best combination of safety ratings, rear climate comfort, and school-run convenience?",
            "I need an EV for daily daycare drop-off and monthly 400-mile family road trips. What brand should I pick?",
            "My kids get motion sickness easily. Which EV has the smoothest acceleration tuning and ride quality for family travel?",
            "Which model has the easiest clean-up for spilled snacks, muddy shoes, and pet hair in a family setting?",
            "If I want max cargo for Costco plus two car seats installed full-time, which brand works best?",
            "What is better for a growing family: Tesla Model Y/Model X route, Rivian R1S, or Lucid SUV plans?",
            "I prioritize rear-seat USB power, quiet cabin for naps, and reliable climate control. Which brand wins?",
            "For suburban family life with occasional ski trips, how should I rank Tesla, Rivian, and Lucid?",
        ],
        "Charging": [
            "I live in Chicago and rely on public fast charging 3 times per week. Which brand gives the least charging friction?",
            "For 900-mile interstate trips, which brand has the most predictable charging stops and shortest total travel time?",
            "I have access to only 120V home charging overnight. Which EV brand is most forgiving with slower home charging?",
            "How do Tesla, Rivian, and Lucid compare in real-world charging curve stability from 10% to 80%?",
            "I want the smallest probability of arriving at a broken charger. Which network experience is best by brand?",
            "If I value transparent battery preconditioning and accurate charge-time estimates, which brand should I trust?",
            "Which EV brand handles winter fast-charging performance best when temperatures are below 20°F?",
            "Can you rank Tesla, Rivian, and Lucid for apartment dwellers who must rely on mixed charging networks?",
            "I need to tow a small trailer occasionally and still fast charge efficiently. Which brand handles that use case best?",
            "For cross-country route planning with charging reliability as #1 priority, what brand should I choose?",
        ],
        "Winter": [
            "I live in Minneapolis with -10°F winters. Which brand keeps the most usable range and cabin comfort?",
            "Which EV handles snow-packed roads better without sacrificing too much battery efficiency: Tesla, Rivian, or Lucid?",
            "For ski season travel with rooftop box and winter tires, which brand remains most practical?",
            "I frequently preheat my car from an outdoor parking lot in freezing weather. Which app + thermal system performs best?",
            "What is the best EV brand for winter reliability if I drive 60 miles daily before sunrise?",
            "In severe winter, which brand has the most dependable defrosting and visibility systems?",
            "Which model line gives the best confidence for icy highway driving and stable regenerative braking control?",
            "I care about winter cabin insulation, steering-wheel heat response, and seat warmth. Which brand excels?",
            "For a Canadian buyer facing long winters and sparse chargers, which brand is safest overall?",
            "If winter range drop is my biggest fear, should I lean Tesla, Rivian, or Lucid in 2026?",
        ],
        "Performance": [
            "I want supercar-like acceleration but still a comfortable daily ride. Which brand nails that balance?",
            "For mountain roads with lots of elevation change, which EV feels most composed under repeated hard driving?",
            "Which brand has the most confidence-inspiring brake feel and thermal management during spirited driving?",
            "I track occasionally and care about repeatable performance, not just 0-60 numbers. Which brand performs best?",
            "Between Tesla Plaid variants, Rivian performance trims, and Lucid high-output models, which is most complete overall?",
            "I need quick passing power at highway speeds with minimal battery drain penalties. Which brand does this best?",
            "Which EV brand has the best steering feel and chassis communication for an enthusiast driver?",
            "For a daily driver that can still be fun on canyon weekends, what should I buy: Tesla, Rivian, or Lucid?",
            "How should I choose if I prioritize acceleration consistency after multiple launches?",
            "Which brand provides the best high-performance value once insurance and tire wear are factored in?",
        ],
        "Safety": [
            "For a parent prioritizing crash protection and active safety tech, which brand is currently strongest?",
            "Which EV has the most trustworthy ADAS behavior in stop-and-go traffic with unpredictable lane merges?",
            "I care about nighttime visibility, emergency braking confidence, and camera clarity. Which brand ranks highest?",
            "For a new driver in the household, which EV ecosystem offers the best safety guardrails and alerts?",
            "How do Tesla, Rivian, and Lucid compare for highway safety when driving in heavy rain?",
            "Which brand provides better real-world reliability for collision-avoidance features?",
            "I need a safe EV for long-distance commuting with occasional driver fatigue. Which system helps the most?",
            "For urban driving with cyclists and tight intersections, which brand's safety stack feels most dependable?",
            "Which EV brand has the strongest blend of passive safety design and practical active-assist tools?",
            "If safety and predictability are above all else, how should I rank Tesla, Rivian, and Lucid?",
        ],
        "Ownership": [
            "Which brand has the smoothest service experience today for warranty repairs: Tesla, Rivian, or Lucid?",
            "I live 120 miles from the nearest service center. Which brand is least risky for maintenance logistics?",
            "For 5-year ownership, which EV brand has the best expected reliability and lowest downtime?",
            "Which brand provides the most transparent communication during recalls and software-related fixes?",
            "If resale value is a major concern, which brand currently appears most resilient in the used market?",
            "How do insurance premiums generally differ between Tesla, Rivian, and Lucid for similar driver profiles?",
            "Which brand has the best owner community and practical support resources when problems happen?",
            "I value fast parts availability and short repair cycles after minor collisions. Which brand is strongest?",
            "What is the smartest long-term ownership choice for someone keeping the EV for 8 years?",
            "Can you recommend a brand based on total ownership stress level, not just specs and price?",
        ],
    }

    prompts: list[tuple[str, str]] = []
    for category, prompts_for_category in prompts_by_category.items():
        if len(prompts_for_category) != 10:
            raise ValueError(
                f"Category {category} expected 10 prompts, got {len(prompts_for_category)}"
            )
        prompts.extend((category, prompt) for prompt in prompts_for_category)

    prompt_texts = [prompt_text for _, prompt_text in prompts]
    if len(prompts) != 100:
        raise ValueError(f"Expected 100 prompts, found {len(prompts)}")
    if len(set(prompt_texts)) != 100:
        raise ValueError("Prompt dataset contains duplicate prompt_text values")

    return prompts


def seed_prompts(reset: bool) -> None:
    prompts = build_prompt_bank()
    with get_connection() as conn:
        init_db(conn)
        existing = prompt_count(conn)

        if existing > 0 and not reset:
            print(
                "Prompts table already contains data. "
                "Re-run with --reset to replace the dataset."
            )
            return

        if reset:
            reset_prompt_related_tables(conn)
            print("Existing prompts/raw responses/parsed metrics removed.")

        insert_prompts(conn, prompts)
        total = prompt_count(conn)
        print(f"Inserted {len(prompts)} prompts. Database now has {total} prompts.")
        print("Category distribution:")
        for row in category_breakdown(conn):
            print(f"  - {row['category']}: {row['total']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate prompts table with 100 EV brand comparison prompts."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing prompt/response data before seeding.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    seed_prompts(reset=args.reset)
