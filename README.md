# LifeLoop solver

Searches for a job/business strategy and prints a monthly action schedule.
The original experimental script is preserved in the initial Git commit.

## Setup and run

Requires Nix with flakes on x86_64 Linux. Python 3.13.15 and its Nix provisioner
input are locked by `flake.nix` and `flake.lock`. The solver and tests use only
the Python standard library; there are no Python packages to install.

Run these commands from the actual checkout or task worktree. They work without
an interactive shell or a previously activated environment:

```bash
nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command python3 --version
nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command python3 -m unittest discover -s tests -v
nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command python3 main.py
```

Nix may download public inputs/binaries on first use. Repeating these commands
reuses its immutable cache and must leave `flake.lock` unchanged. No virtualenv,
mutable dependency directory, credentials, or deployment setup is needed.

The default scenario uses maximum education (DocuDyno), the business starting
bonus, nine business slots, and a lifespan of 90 years. Choose a scenario with:

```bash
nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file --command python3 main.py --education freshmart --starting-bonus job --beam-width 128
```

Education choices: `sunny-sprout`, `freshmart`, `brickline`, `bytefix`, `docudyno`.
Starting bonus choices: `job`, `business`.

## Game rules

- Education determines the job track and starting age: 10, 12, 17, 19, or 22.
- Choose a permanent +100% job or business income bonus (2× base). Market is omitted.
- Own up to nine businesses, including multiple copies of the same business.
- All sixteen business tiers are included, from Green Fork ($3,000, $35/month)
  through Bright Core ($13,790,000, $35,500/month).
- Activate the job boost once and the independent business boost once per round.
  Each doubles its income category for 120 monthly payments (ten years).
  This multiplies the starting bonus for 4× base income in that category.
- Normally a sale refunds 70% of purchase price. One business sale per round can
  instead refund 140%. Other copies and subsequent sales receive 70%.
- DocuDyno upgrades to $400 base monthly pay during age 71 years, six months.
  The first $400 payment arrives at 71 years, seven months.

Age labels such as `71y06m` are years and months, never decimal years.
Boosts activate before that month's payment. Income arrives before purchases
and sales, so a newly bought business first earns next month. Paid months begin
one month after education finishes and end before age 90. Remaining businesses
are sold at age 90; if the refund boost is unused, it applies to one most
expensive remaining business. Multiple copies and final liquidation retain the
prototype's existing assumptions. The model also assumes a sold business can
be purchased again.

## Search limits

This is a bounded beam search, **not a proof of the globally optimal strategy**.
It considers boost activation each month and retains the best estimated states
according to `--beam-width` (default 64). A wider beam costs more time and memory;
it can produce a different result and does not guarantee improvement.

The planner explores waiting, one purchase, one normal upgrade to a higher
income business, or one boosted sale optionally followed by a purchase per
month. The replay model permits multiple trades in a month. This action limit
belongs to the search, not the game rules. Beam ranking estimates holding
current businesses through the remaining lifespan, including available boosts.
It can discard strategies that would become stronger through later purchases.

Every printed strategy is replayed against the monthly game model before its
result is shown. Dollar calculations use integers; the catalog's whole-thousand
prices make 70% and 140% refunds exact.

`lifeloop/model.py` owns the rules and replay; `lifeloop/solver.py` owns strategy
search. Project plans, tickets, and rule decisions live in SilverBullet under
`Projects/Lifeloop`.
