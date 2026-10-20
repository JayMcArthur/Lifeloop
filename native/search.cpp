#include "safety.hpp"

#include <array>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <tuple>
#include <unordered_map>
#include <vector>

using Money = std::int64_t;
constexpr int job_boost = 0, business_boost = 1, buy = 2, sell = 3, refund = 4;
volatile std::sig_atomic_t interrupted = 0;

struct Action { int month, kind, business; };
struct Trace { Action action; std::shared_ptr<const Trace> parent; };
struct Business { Money cost, income; };
struct State {
    std::uint64_t holdings = 0;
    Money cash = 0, rate = 0, resale = 0, extra_refund = 0;
    int count = 0, job_end = 0, business_end = 0;
    bool refund_used = false;
    std::shared_ptr<const Trace> path;
};
struct Key {
    std::uint64_t holdings;
    int job_clock, business_clock;
    bool refund_used;
    bool operator==(const Key&) const = default;
};
struct KeyHash {
    std::size_t operator()(const Key& key) const {
        auto hash = key.holdings;
        hash ^= std::uint64_t(key.job_clock) * 0x9e3779b97f4a7c15ULL;
        hash ^= std::uint64_t(key.business_clock) * 0xbf58476d1ce4e5b9ULL;
        return hash ^ (key.refund_used ? 0x94d049bb133111ebULL : 0);
    }
};
using Pool = std::unordered_map<Key, State, KeyHash>;

struct Input {
    int first, end, slots, width, seconds, memory_mb, diversity, income_weight, business_count;
    Money cash, seed_cash;
    std::vector<Business> businesses;
    std::vector<Money> payments, prefix;
    std::vector<Action> seed;
};

Input read_input() {
    Input input{};
    std::string magic;
    std::cin >> magic >> input.first >> input.end >> input.slots >> input.width >> input.seconds
             >> input.memory_mb >> input.diversity >> input.income_weight >> input.cash >> input.business_count;
    if (!std::cin || magic != "LIFELOOP1" || input.first < 1 || input.end < input.first ||
        input.end > 1080 || input.slots < 1 || input.slots > 9 || input.width < 1 || input.width > 50000 ||
        input.seconds < 1 || input.seconds > 1700 || input.memory_mb < 64 || input.memory_mb > 768 ||
        input.diversity < 0 || input.diversity > 1 || input.income_weight < 25 || input.income_weight > 200 ||
        input.cash < 0 || input.cash > 1'000'000'000'000LL || input.business_count < 1 || input.business_count > 16)
        throw std::runtime_error("Invalid bounded search input");
    for (int i = 0; i < input.business_count; ++i) {
        Business business{};
        std::cin >> business.cost >> business.income;
        if (!std::cin || business.cost < 10 || business.cost > 1'000'000'000'000LL ||
            business.cost % 10 || business.income < 1 || business.income > 1'000'000'000)
            throw std::runtime_error("Invalid business price or income");
        input.businesses.push_back(business);
    }
    input.prefix.push_back(0);
    for (int i = 0; i < input.end; ++i) {
        Money payment = 0;
        std::cin >> payment;
        if (!std::cin || payment < 0 || payment > 1'000'000'000)
            throw std::runtime_error("Invalid monthly payment");
        if (!input.payments.empty() && payment < input.payments.back())
            throw std::runtime_error("Pay schedules must be nondecreasing");
        input.payments.push_back(payment);
        input.prefix.push_back(input.prefix.back() + payment);
    }
    int seed_count = 0;
    std::cin >> input.seed_cash >> seed_count;
    if (!std::cin || seed_count < 0 || seed_count > 50000) throw std::runtime_error("Invalid seed size");
    for (int i = 0; i < seed_count; ++i) {
        Action action{};
        std::cin >> action.month >> action.kind >> action.business;
        if (!std::cin || action.month < input.first || action.month >= input.end ||
            action.kind < 0 || action.kind > 4 || (i && action.month < input.seed.back().month))
            throw std::runtime_error("Invalid seed action");
        input.seed.push_back(action);
    }
    return input;
}

struct Stop { const char* reason; };

class Search {
    Input input;
    std::chrono::steady_clock::time_point started = std::chrono::steady_clock::now();
    std::vector<Action> best_actions;
    Money best_cash = -1;
    std::uint64_t candidates = 0, dominated = 0, pruned = 0;
    std::size_t peak_pool = 0;
    int completed_months = 0;
    bool depth_limited = false, seeded_best = false;
    const char* status = "completed";

    Key key(const State& state, int month) const {
        // 0 means unused, 1 means consumed/expired; only future active months matter.
        return {state.holdings, state.job_end ? std::max(1, state.job_end - month) : 0,
                state.business_end ? std::max(1, state.business_end - month) : 0, state.refund_used};
    }

    int lane(const State& state) const {
        return (!state.job_end) | ((!state.business_end) << 1) | ((!state.refund_used) << 2);
    }

    Money completion(const State& state, int month) const {
        const int next = month + 1, remaining = input.end - next;
        Money value = state.cash + state.resale + state.rate * remaining + input.prefix[input.end] - input.prefix[next];
        if (!state.refund_used) value += state.extra_refund;
        if (!state.job_end) value += input.prefix[input.end] - input.prefix[std::max(next, input.end - 120)];
        else value += input.prefix[std::max(next, std::min(input.end, state.job_end))] - input.prefix[next];
        const int boost_months = state.business_end ? std::max(0, std::min(input.end, state.business_end) - next)
                                                   : std::min(120, remaining);
        return value + state.rate * boost_months;
    }

    long double score(const State& state, int month) const {
        const Money future_business = state.rate * (input.end - month - 1);
        return completion(state, month) + future_business * (input.income_weight - 100) / 100.0L;
    }

    void keep_completion(const State& state, int month) {
        const Money value = completion(state, month);
        if (value <= best_cash) return;
        best_cash = value;
        seeded_best = false;
        best_actions.clear();
        for (auto path = state.path; path; path = path->parent) best_actions.push_back(path->action);
        std::reverse(best_actions.begin(), best_actions.end());
        std::vector<Action> tail;
        const int next = month + 1;
        if (!state.job_end && next < input.end)
            tail.push_back({std::max(next, input.end - 120), job_boost, -1});
        if (!state.business_end && state.count && next < input.end)
            tail.push_back({next, business_boost, -1});
        std::stable_sort(tail.begin(), tail.end(), [](auto a, auto b) { return a.month < b.month; });
        best_actions.insert(best_actions.end(), tail.begin(), tail.end());
    }

    void check_budget() const {
        if (interrupted) throw Stop{"interrupted"};
        const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
        if (elapsed >= input.seconds) throw Stop{"time_limit"};
        if (peak_rss_kb() >= input.memory_mb * 1024L) throw Stop{"memory_limit"};
    }

    State act(State state, Action action) const {
        const int i = action.business;
        if (action.kind < buy) {
            int& until = action.kind == job_boost ? state.job_end : state.business_end;
            if (until) throw std::runtime_error("Seed reuses income boost");
            until = action.month + 120;
        } else {
            if (i < 0 || i >= input.business_count) throw std::runtime_error("Unknown seed business");
            const auto& business = input.businesses[i];
            const auto unit = std::uint64_t(1) << (4 * i);
            if (action.kind == buy) {
                if (state.cash < business.cost || state.count >= input.slots)
                    throw std::runtime_error("Unaffordable seed purchase");
                state.cash -= business.cost;
                state.holdings += unit;
                state.count++;
                state.rate += business.income;
                state.resale += business.cost * 7 / 10;
            } else {
                if (!((state.holdings >> (4 * i)) & 15) || (action.kind == refund && state.refund_used))
                    throw std::runtime_error("Invalid seed sale");
                state.cash += business.cost * (action.kind == refund ? 14 : 7) / 10;
                state.holdings -= unit;
                state.count--;
                state.rate -= business.income;
                state.resale -= business.cost * 7 / 10;
                state.refund_used = state.refund_used || action.kind == refund;
            }
            state.extra_refund = 0;
            for (int j = 0; j < input.business_count; ++j) {
                if ((state.holdings >> (4 * j)) & 15)
                    state.extra_refund = std::max(state.extra_refund, input.businesses[j].cost * 7 / 10);
            }
        }
        state.path = std::make_shared<Trace>(Trace{action, state.path});
        return state;
    }

    State pay(State state, int month) const {
        state.cash += input.payments[month] * (month < state.job_end ? 2 : 1);
        state.cash += state.rate * (month < state.business_end ? 2 : 1);
        return state;
    }

    std::vector<State> select(Pool& pool, int month) {
        std::vector<State> ordered;
        ordered.reserve(pool.size());
        for (auto& [unused, state] : pool) ordered.push_back(std::move(state));
        pool.clear();
        std::sort(ordered.begin(), ordered.end(), [&](const State& a, const State& b) {
            const auto a_score = score(a, month), b_score = score(b, month);
            if (a_score != b_score) return a_score > b_score;
            return std::tie(a.cash, a.holdings, a.job_end, a.business_end, a.refund_used) >
                   std::tie(b.cash, b.holdings, b.job_end, b.business_end, b.refund_used);
        });
        if (ordered.size() <= std::size_t(input.width)) return ordered;
        pruned += ordered.size() - input.width;
        std::vector<State> selected;
        selected.reserve(input.width);
        std::vector<bool> used(ordered.size(), false);
        std::array<int, 8> counts{};
        const int quota = input.diversity ? input.width / 16 : 0;
        for (std::size_t i = 0; i < ordered.size(); ++i) {
            if (counts[lane(ordered[i])] < quota) {
                counts[lane(ordered[i])]++;
                used[i] = true;
                selected.push_back(ordered[i]);
            }
        }
        for (std::size_t i = 0; i < ordered.size() && selected.size() < std::size_t(input.width); ++i)
            if (!used[i]) selected.push_back(std::move(ordered[i]));
        return selected;
    }

    bool offer(Pool& pool, State state, int month) {
        if ((++candidates & 1023) == 0) check_budget();
        const Key identity = key(state, month);
        auto found = pool.find(identity);
        if (found != pool.end() && found->second.cash >= state.cash) {
            dominated++;
            return false;
        }
        keep_completion(state, month);
        pool.insert_or_assign(identity, std::move(state));
        peak_pool = std::max(peak_pool, pool.size());
        if (pool.size() >= std::size_t(input.width) * 2) {
            auto retained = select(pool, month);
            for (auto& item : retained) pool.emplace(key(item, month), std::move(item));
        }
        return true;
    }

public:
    explicit Search(Input data) : input(std::move(data)) {}

    void run() {
        State initial;
        initial.cash = input.cash;
        keep_completion(initial, input.first - 1);
        State seed_state = initial;
        std::size_t seed_index = 0;
        // Validate the full seed before accepting its claimed final value.
        if (input.seed_cash >= 0) {
            for (int month = input.first; month < input.end; ++month) {
                bool traded = false;
                auto index = seed_index;
                while (index < input.seed.size() && input.seed[index].month == month) {
                    const auto action = input.seed[index++];
                    if (action.kind < buy) {
                        if (traded) throw std::runtime_error("Seed boosts follow trades");
                        seed_state = act(seed_state, action);
                    } else traded = true;
                }
                seed_state = pay(seed_state, month);
                while (seed_index < input.seed.size() && input.seed[seed_index].month == month) {
                    const auto action = input.seed[seed_index++];
                    if (action.kind >= buy) seed_state = act(seed_state, action);
                }
            }
            const Money seed_value = seed_state.cash + seed_state.resale +
                                     (seed_state.refund_used ? 0 : seed_state.extra_refund);
            if (seed_index != input.seed.size() || seed_value != input.seed_cash)
                throw std::runtime_error("Seed does not replay to its claimed value");
            if (seed_value > best_cash) {
                best_cash = seed_value;
                best_actions = input.seed;
                seeded_best = true;
            }
        }
        seed_state = initial;
        seed_index = 0;
        std::vector<State> beam{initial};
        try {
            for (int month = input.first; month < input.end; ++month) {
                check_budget();
                Pool pool;
                pool.reserve(std::size_t(input.width) * 2);
                for (const auto& state : beam) {
                    std::vector<State> choices{state};
                    if (!state.job_end) choices.push_back(act(state, {month, job_boost, -1}));
                    if (!state.business_end && state.count) {
                        const auto size = choices.size();
                        for (std::size_t i = 0; i < size; ++i)
                            choices.push_back(act(choices[i], {month, business_boost, -1}));
                    }
                    for (auto& choice : choices) offer(pool, pay(std::move(choice), month), month);
                }
                if (input.seed_cash >= 0) {
                    auto index = seed_index;
                    while (index < input.seed.size() && input.seed[index].month == month) {
                        const auto action = input.seed[index++];
                        if (action.kind < buy) seed_state = act(seed_state, action);
                    }
                    seed_state = pay(seed_state, month);
                    while (seed_index < input.seed.size() && input.seed[seed_index].month == month) {
                        const auto action = input.seed[seed_index++];
                        if (action.kind >= buy) seed_state = act(seed_state, action);
                    }
                    offer(pool, seed_state, month);
                }
                auto retained = select(pool, month);
                // Positive-cost ordinary cycles are cash-dominated. A normal
                // trade form needs <=9 old sales, <=9 buys and one refund cycle.
                bool converged = false;
                for (int depth = 0; depth < 20; ++depth) {
                    for (const auto& state : retained) pool.emplace(key(state, month), state);
                    bool changed = false;
                    for (const auto& state : retained) {
                        for (int i = 0; i < input.business_count; ++i) {
                            if (state.count < input.slots && state.cash >= input.businesses[i].cost)
                                changed = offer(pool, act(state, {month, buy, i}), month) || changed;
                            if ((state.holdings >> (4 * i)) & 15) {
                                changed = offer(pool, act(state, {month, sell, i}), month) || changed;
                                if (!state.refund_used)
                                    changed = offer(pool, act(state, {month, refund, i}), month) || changed;
                            }
                        }
                    }
                    retained = select(pool, month);
                    if (!changed) { converged = true; break; }
                }
                depth_limited = depth_limited || !converged;
                beam = std::move(retained);
                completed_months++;
            }
        } catch (const Stop& stop) { status = stop.reason; }
    }

    void report() const {
        const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
        const bool complete = completed_months == input.end - input.first;
        std::cout << "{\"final_cash\":" << best_cash << ",\"actions\":[";
        for (std::size_t i = 0; i < best_actions.size(); ++i) {
            if (i) std::cout << ',';
            const auto action = best_actions[i];
            std::cout << '[' << action.month << ',' << action.kind << ',' << action.business << ']';
        }
        std::cout << "],\"statistics\":{\"engine\":\"cpp\",\"status\":\"" << status
                  << "\",\"elapsed_seconds\":" << elapsed << ",\"peak_rss_kb\":" << peak_rss_kb()
                  << ",\"candidates\":" << candidates << ",\"dominated\":" << dominated
                  << ",\"lossy_prunes\":" << pruned << ",\"peak_pool\":" << peak_pool
                  << ",\"months_completed\":" << completed_months
                  << ",\"depth_limited\":" << (depth_limited ? "true" : "false")
                  << ",\"certified\":" << (complete && !pruned && !depth_limited ? "true" : "false")
                  << ",\"best_source\":\"" << (seeded_best ? "incumbent" : "search") << "\"}}\n";
    }
};

int main(int argc, char** argv) {
    JobLimits limits;
    if (!install_safety(limits)) {
        std::cerr << "A verified bounded LifeLoop cgroup is required; use scripts/run_safe.sh\n";
        return 2;
    }
    if (argc == 2 && std::string(argv[1]) == "--safety-report") {
        rlimit address{}, cpu{}, core{};
        getrlimit(RLIMIT_AS, &address); getrlimit(RLIMIT_CPU, &cpu); getrlimit(RLIMIT_CORE, &core);
        std::cout << "{\"address_space\":" << address.rlim_cur << ",\"cpu_seconds\":" << cpu.rlim_cur
                  << ",\"core_bytes\":" << core.rlim_cur << ",\"job_memory\":" << limits.memory
                  << ",\"job_swap\":" << limits.swap << ",\"cpu_quota\":" << limits.quota
                  << ",\"cpu_period\":" << limits.period << ",\"tasks\":" << limits.tasks
                  << ",\"oom_group\":" << limits.oom_group << "}\n";
        return 0;
    }
    std::signal(SIGTERM, [](int) { interrupted = 1; });
    std::signal(SIGINT, [](int) { interrupted = 1; });
    try {
        Search search(read_input());
        search.run();
        search.report();
    } catch (const std::exception& error) {
        std::cerr << "Native search failed: " << error.what() << '\n';
        return 2;
    }
}
