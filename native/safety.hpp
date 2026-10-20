#pragma once

#include <algorithm>
#include <fstream>
#include <iostream>
#include <string>
#include <sys/resource.h>

struct JobLimits {
    long long memory = 0, swap = -1, quota = 0, period = 0, tasks = 0, oom_group = 0;
};

inline bool lower_limit(int resource, rlim_t requested) {
    rlimit current{};
    if (getrlimit(resource, &current) != 0) return false;
    const auto hard = std::min(current.rlim_max, requested);
    const rlimit desired{std::min(current.rlim_cur, hard), hard};
    return setrlimit(resource, &desired) == 0;
}

inline bool install_safety(JobLimits& limits) {
    if (!lower_limit(RLIMIT_AS, 1024ULL * 1024 * 1024) ||
        !lower_limit(RLIMIT_CPU, 1800) || !lower_limit(RLIMIT_CORE, 0)) return false;
    std::ifstream membership("/proc/self/cgroup");
    std::string line, path;
    while (std::getline(membership, line)) {
        if (line.starts_with("0::")) path = line.substr(3);
    }
    const auto name = path.substr(path.find_last_of('/') + 1);
    if (!name.starts_with("lifeloop-limited-") || !name.ends_with(".scope")) return false;
    const auto root = "/sys/fs/cgroup" + path;
    std::ifstream(root + "/memory.max") >> limits.memory;
    std::ifstream(root + "/memory.swap.max") >> limits.swap;
    std::ifstream(root + "/cpu.max") >> limits.quota >> limits.period;
    std::ifstream(root + "/pids.max") >> limits.tasks;
    std::ifstream(root + "/memory.oom.group") >> limits.oom_group;
    return limits.memory > 0 && limits.memory <= 1024LL * 1024 * 1024 && limits.swap == 0 &&
           limits.quota > 0 && limits.quota <= limits.period && limits.tasks > 0 &&
           limits.tasks <= 64 && limits.oom_group == 1;
}

inline long peak_rss_kb() {
    rusage usage{};
    getrusage(RUSAGE_SELF, &usage);
    return usage.ru_maxrss;
}
