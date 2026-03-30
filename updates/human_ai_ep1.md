# Humans & AI [Ep. 1] - Gigachad Strikes

*November 5, 2025* · AI vs. Human showdown - who comes out on top?

We're particularly excited about using CodeClash as a platform to explore collaboration and competition among human and AI programmers.

In the inaugural blog post of this series, we aim to answer a simple question: *Where does AI rank among human competitors?*

We decided, the simplest way to address this, is find top-ranked, human-written submissions from existing leaderboards and pit them against LMs.

## Finding Top Submissions

To investigate this, we scoured the web for online leaderboards of the code arenas supported in CodeClash.
This was surprisingly challenging:

* We couldn't find leaderboards for some arenas ([Core War](/arenas/corewar/), [RoboCode](/arenas/robocode/)).
* [Poker (HuskyBench)](/arenas/poker/) has a great [website](https://huskybench.com/), but as an LM evaluation, there's no human-written submissions.
* [Halite](/arenas/halite/) probably has a leaderboard somewhere, but we couldn't find it. The one on the [resurrected website](https://halite-tournament.fly.dev/leaderboard/) seems to be filled with test bots.
    * Halite III (which we'll support soon) has a Kaggle [leaderboard](https://www.kaggle.com/c/halite/leaderboard).
* [BattleSnake](https://play.battlesnake.com/leaderboards) has an awesome, active official leaderboard with ranked submissions. *But* most submissions are closed source, and we couldn't find a way to filter for open source bots only.

[RobotRumble](/arenas/robotrumble/) ended up being the only arena with a [leaderboard](https://robotrumble.org/boards/2) that fit our search criteria:

* Has many human-written submissions
* The submissions are ranked
* Some submissions are open source

<img src="images/leaderboard_20251031.png" class="img-insight" />

As of October 31, 2025, the top-ranked open-source submission on RobotRumble is
<img src="images/gigachad.jpg" class="img-inline" style="height:1.2rem;margin-right:0em;" />
**gigachad** by user **entropic-drifter** ([link](https://robotrumble.org/entropicdrifter/gigachad)).

## The Showdown

We ran CodeClash tournaments between <img src="images/gigachad.jpg" class="img-inline" style="height:1.2rem;margin-right:0em;" />
**gigachad** and Claude Sonnet 4.5, the top ranked LM on RobotRumble as of 11/2025.
The details:

* Ran 10 tournaments of 15 rounds each
* Each round's competition phase ran 250 simulations
* Claude 4.5 Sonnet was ran with temperature 0.2 and max tokens 4096
* Claude 4.5 Sonnet uses [mini-swe-agent](https://mini-swe-agent.com/latest/) as the agent scaffold
* On the other hand, <img src="images/gigachad.jpg" class="img-inline" style="height:1.2rem;margin-right:0em;" />
**gigachad** is held *constant* across all tournaments. In other words, no human or LM is optimizing **gigachad** between rounds.

We were pretty surprised by the results.

True to its namesake,
<img src="images/gigachad.jpg" class="img-inline" style="height:1.2rem;margin-right:0em;" /> **gigachad**
dominates Claude Sonnet 4.5, winning

* 10/10 tournaments
* 150/150 rounds
* 37,500/37,500 simulations

<img src="images/scoreboard.png" class="img-insight" style="width:100%" />

We didn't necessarily expect Claude Sonnet 4.5 to write a better bot than <img src="images/gigachad.jpg" class="img-inline" style="height:1.2rem;margin-right:0em;" />
**gigachad**, but what surprised us was the *magnitude* of the difference.

## What went wrong?

In our original paper, we discuss several weaknesses with regards to LMs as long-horizon, self-improving developers:

1. Model codebases become messier over time without proper refactoring
    * Models don't really reuse or build on files
    * Models generate a lot of redundant, single-use code
    * Models dump all these files in the root directory, rather than organize them into folders
2. Models don't draw insights from prior runs effectively. Models *do* look at competition logs, but the analysis is often shallow, such as just reading the first couple lines or calculating win rate. But it won't...
    * Understand the format of logs deeply (e.g., by reading docs)
    * Look at multiple logs together to identify patterns
3. Models draw questionable conclusions from their insights

From these runs, we see these weaknesses clearly manifested.

**1. Messy Codebases**: Claude Sonnet 4.5 creates 33 files by the end of the tournament ([PR](https://github.com/emagedoc/RobotRumble/compare/main...PvpTournament.RobotRumble.r15.s250.p2.claude-sonnet-4-5-20250929.human.251101155558.claude-sonnet-4-5-20250929)).

* `analyze_logs.py`, `analyze_round.py` are a bit redundant.
* `check_spawn*.py` could be combined.
* `combat_analysis.py`, `detailed_analysis.py` overlap in functionality.

<img src="images/codebase.png" class="img-insight" />

**2. Shallow Analysis**: In this tournament, Claude Sonnet 4.5 does reuse the `analyze_logs.py` (yay!), but the analysis is somewhat shallow.

* It only looks at three simulations (first/middle/last) of each round.
* It just summarizes scores and winners, which is technically already in `results.json`.
* The analysis states facts (e.g., winner, initial/final units), but there's not much around *why* units were lost or *how* a competition actually unfolded.

<details>
<summary>Show `analyze_logs.py` code</summary>
<pre class="prettyprint lang-py">
import json
import os
from collections import defaultdict

def analyze_simulation(sim_file):
    """Analyze a single simulation file"""
    with open(sim_file, 'r') as f:
        data = json.load(f)
    winner = data.get('winner', 'Unknown')
    turns = data.get('turns', [])
    if not turns:
        return None
    # Get initial and final state
    initial_state = turns[0]['state']
    final_state = turns[-1]['state']
    # Count units by team
    def count_units(state):
        red_units = 0
        blue_units = 0
        for obj in state['objs'].values():
            if obj.get('obj_type') == 'Unit':
                if obj.get('team') == 'Red':
                    red_units += 1
                elif obj.get('team') == 'Blue':
                    blue_units += 1
        return red_units, blue_units
    initial_red, initial_blue = count_units(initial_state)
    final_red, final_blue = count_units(final_state)
    return {
        'winner': winner,
        'turns': len(turns),
        'initial_red': initial_red,
        'initial_blue': initial_blue,
        'final_red': final_red,
        'final_blue': final_blue
    }

def analyze_round(round_dir):
    """Analyze all simulations in a round"""
    results_file = os.path.join(round_dir, 'results.json')
    if not os.path.exists(results_file):
        print(f"No results.json found in {round_dir}")
        return
    with open(results_file, 'r') as f:
        results = json.load(f)
    print(f"\n=== Round {results['round_num']} Results ===")
    print(f"Winner: {results['winner']}")
    print(f"Scores: {results['scores']}")
    # Analyze a few sample simulations
    sim_files = [f for f in os.listdir(round_dir) if f.startswith('sim_') and f.endswith('.json')]
    sim_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    print(f"\nTotal simulations: {len(sim_files)}")
    # Sample first, middle, and last simulations
    samples = []
    if len(sim_files) > 0:
        samples.append(sim_files[0])
    if len(sim_files) > 1:
        samples.append(sim_files[len(sim_files)//2])
    if len(sim_files) > 2:
        samples.append(sim_files[-1])
    print("\nSample simulations:")
    for sim_file in samples:
        sim_path = os.path.join(round_dir, sim_file)
        analysis = analyze_simulation(sim_path)
        if analysis:
            print(f"\n{sim_file}:")
            print(f"  Winner: {analysis['winner']}")
            print(f"  Turns: {analysis['turns']}")
            print(f"  Initial units - Red: {analysis['initial_red']}, Blue: {analysis['initial_blue']}")
            print(f"  Final units - Red: {analysis['final_red']}, Blue: {analysis['final_blue']}")

if __name__ == '__main__':
    logs_dir = '/logs/rounds'
    # Find all round directories
    round_dirs = []
    for item in os.listdir(logs_dir):
        item_path = os.path.join(logs_dir, item)
        if os.path.isdir(item_path):
            round_dirs.append(item_path)
    round_dirs.sort()
    for round_dir in round_dirs:
        analyze_round(round_dir)
</pre>
</details>

One could imagine analyses that dig deeper, such as...

* Seeing how opponent units are behaving (are they clustering around weak units? How do opponents' healthy vs. damaged units behave differently?)
* Write analyses that digest simulations from multiple rounds.

**3. Misinterpretations**: Finally, a snippet of some fairly crucial mis-interpretations of prior results:

<img src="images/missteps.png" class="img-insight" />

> THOUGHT (Step 4): Interesting! The pattern shows that we (Blue) won in rounds 1, 3, 4, and 7, but lost in rounds 0, 2, 5, and 6. It seems like we're alternating - when we're Blue we win (spawn avoidance works), but when we're Red we lose (opponent has spawn avoidance).

This is incorrect.
<img src="images/gigachad.jpg" class="img-inline" style="height:1.2rem;margin-right:0em;" /> **gigachad** wins every single round.
Colors are assigned randomly each round, so there's no correlation.
In `results.json`, there's explicitly a line that clarifies this:

`In this round, claude-sonnet-4-5-20250929 was Blue and human was Red.`

> ACTION (Step 4): `cd /workspace && for i in 1 50 100 150 200; do echo "=== sim_$i.json ==="; python detailed_analysis.py /logs/rounds/7/sim_$i.json | head -20; done`

The analysis again just samples a handful of simulations.
This is arguably okay, but...

> THOUGHT (Step 5): Perfect! All sampled games show Blue (us) winning consistently with 40 units vs Red's 3-4 units. The spawn avoidance is working well...

This is unfortunately the wrong conclusion.
Given this flawed insight, the rest of the changes this round are, as shown, not effective.

## Concluding Thoughts

A surprising result indeed!

* As benchmark builders, it's great to identify room for growth.
* As model trainers, we think this is signal that CodeClash's goal-oriented rewards can be very useful for post-training.

Next, we're interested in...

* Repeating this process for other arenas. Did we overlook a submission or leaderboard? Create an issue in our [GitHub repo](https://github.com/emagedoc/CodeClash) if you spot one!
* Studying human-AI collaboration/competition dynamics requires careful experimental design and recruitment. We're exploring ways to do this meaningfully at scale (<a href="/team/">email us</a> if you're interested!)

For now, <img src="images/gigachad.jpg" class="img-inline" style="height:1.2rem;margin-right:0em;" /> **gigachad** remains formidable.
Until next time!

P.S. here is the `robot.py` Claude Sonnet 4.5 wrote by the 15th round.
It did come up with some clever strategies from the get-go, but it's the ability to build-over-time that leaves more to be desired.

<details>
<summary>Show `robot.py` code</summary>
<pre class="prettyprint lang-py">
"""
Round 15 - Improved spawn clearing and more aggressive combat
- Start clearing at turn 3 (earlier than turn 5)
- ALL units avoid spawn points during clearing window
- More aggressive combat to maintain unit superiority
"""

def get_robots_for_team(state, team):
    """Get all units for a team."""
    return [obj for obj in state.objs_by_team(team)]

def get_nearby_units(unit, units, radius=5):
    """Get units within radius of given unit."""
    return [u for u in units if unit.coords.distance_to(u.coords) <= radius]

def find_weakest_adjacent_enemy(unit, enemies):
    """Find the weakest adjacent enemy to attack."""
    adjacent = [(e, unit.coords.direction_to(e.coords))
                for e in enemies
                if unit.coords.distance_to(e.coords) == 1]

    if not adjacent:
        return None

    adjacent.sort(key=lambda x: x[0].health)
    return adjacent[0][1]

def get_direction_counts(unit, units):
    """Count how many units are in each direction."""
    direction_counts = {}
    for u in units:
        if u.id == unit.id:
            continue
        direction = unit.coords.direction_to(u.coords)
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
    return direction_counts

def get_most_common_directions(unit, units):
    """Get directions with most units."""
    counts = get_direction_counts(unit, units)
    if not counts:
        return []

    max_count = max(counts.values())
    return [d for d, c in counts.items() if c == max_count]

def is_move_valid(state, unit, direction):
    """Check if we can move in a direction."""
    try:
        new_coords = unit.coords + direction
        obj = state.obj_by_coords(new_coords)
        return obj is None
    except:
        return False

def get_move_toward_center(state, unit):
    """Get a move that takes us toward the center of the map (away from spawn points)."""
    # Map center is around (9, 9)
    center_x, center_y = 9, 9

    # Determine which direction moves us closer to center
    dx = center_x - unit.coords.x
    dy = center_y - unit.coords.y

    # Prioritize the larger difference
    directions = []
    if abs(dx) >= abs(dy):
        if dx > 0:
            directions.append(Direction.East)
        elif dx < 0:
            directions.append(Direction.West)
        if dy > 0:
            directions.append(Direction.South)
        elif dy < 0:
            directions.append(Direction.North)
    else:
        if dy > 0:
            directions.append(Direction.South)
        elif dy < 0:
            directions.append(Direction.North)
        if dx > 0:
            directions.append(Direction.East)
        elif dx < 0:
            directions.append(Direction.West)

    # Try directions that move toward center and avoid spawn points
    for direction in directions:
        if is_move_valid(state, unit, direction):
            new_coords = unit.coords + direction
            if not new_coords.is_spawn():
                return direction

    # If can't move toward center without spawn, try any non-spawn move
    all_directions = [Direction.North, Direction.South, Direction.East, Direction.West]
    for direction in all_directions:
        if is_move_valid(state, unit, direction):
            new_coords = unit.coords + direction
            if not new_coords.is_spawn():
                return direction

    # Last resort: move anywhere
    for direction in all_directions:
        if is_move_valid(state, unit, direction):
            return direction

    return None

def robot(state, unit):
    """Main robot logic."""
    turn_in_cycle = state.turn % 10

    # CRITICAL: Clear spawn points before spawn turns
    # Spawns happen at turn 0, 10, 20, 30, etc.
    # Start clearing at turn 3 to ensure spawn points are clear
    is_near_spawn_time = (turn_in_cycle >= 3)

    # If we're on a spawn point during clearing window, MUST move off
    if is_near_spawn_time and unit.coords.is_spawn():
        move_dir = get_move_toward_center(state, unit)
        if move_dir:
            return Action.move(move_dir)
        # If completely blocked, do nothing
        return None

    # Get all units
    our_robots = get_robots_for_team(state, state.our_team)
    enemy_robots = get_robots_for_team(state, state.other_team)

    if not enemy_robots:
        return None

    # Calculate aggressive multiplier - be more aggressive overall
    # Increase aggression near spawn time to push enemies away
    spawn_multiplier = 2.5 if turn_in_cycle >= 7 else 1.5
    health_multiplier = 0.5 if unit.health <= 2 else 1.0
    aggressive_multiplier = spawn_multiplier * health_multiplier

    # Get nearby units
    nearby_allies = get_nearby_units(unit, our_robots, radius=5)
    nearby_enemies = get_nearby_units(unit, enemy_robots, radius=5)

    # Calculate local strength
    ally_strength = len(nearby_allies) + sum(a.health for a in nearby_allies) / 5.0
    enemy_strength = len(nearby_enemies) + sum(e.health for e in nearby_enemies) / 5.0

    # Find adjacent enemy
    adjacent_enemy_dir = find_weakest_adjacent_enemy(unit, nearby_enemies)

    # If outnumbered locally, try to flee
    if ally_strength * aggressive_multiplier < enemy_strength:
        enemy_directions = get_most_common_directions(unit, nearby_enemies)
        flee_directions = [d.opposite for d in enemy_directions]

        ally_directions = get_most_common_directions(unit, nearby_allies)

        # Prefer directions away from enemies and toward allies
        common_directions = [d for d in flee_directions if d in ally_directions]

        # During clearing window, avoid spawn points
        for direction in common_directions:
            if is_move_valid(state, unit, direction):
                new_coords = unit.coords + direction
                if not is_near_spawn_time or not new_coords.is_spawn():
                    return Action.move(direction)

        # Just flee away from enemies
        for direction in flee_directions:
            if is_move_valid(state, unit, direction):
                new_coords = unit.coords + direction
                if not is_near_spawn_time or not new_coords.is_spawn():
                    return Action.move(direction)

        # Attack if adjacent
        if adjacent_enemy_dir:
            return Action.attack(adjacent_enemy_dir)

        return None

    # We have local advantage, be aggressive

    # Attack if adjacent
    if adjacent_enemy_dir:
        return Action.attack(adjacent_enemy_dir)

    # Move toward nearest enemy
    if enemy_robots:
        nearest_enemy = min(enemy_robots, key=lambda e: unit.coords.distance_to(e.coords))
        move_direction = unit.coords.direction_to(nearest_enemy.coords)

        # Try to move, rotating if blocked
        for _ in range(4):
            if is_move_valid(state, unit, direction):
                new_coords = unit.coords + move_direction
                # During clearing window, avoid spawn points
                if not is_near_spawn_time or not new_coords.is_spawn():
                    return Action.move(move_direction)
            move_direction = move_direction.rotate_cw

    return None
</pre>
