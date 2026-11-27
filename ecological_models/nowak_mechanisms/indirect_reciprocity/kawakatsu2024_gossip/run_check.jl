## run_check.jl: driver for PREREGISTRATION.md (Kawakatsu, Kessinger and Plotkin 2024 as an external check).
##
## Uses the authors' NeutralGossip module unchanged (commit 9d894a7, cloned outside this repository). Parameters are
## constants here (per AGENTS.md); the stage entry scripts run_stage1.jl, run_stage2.jl and run_stage3.jl call
## run_stage(k). Each run seeds Julia's global stream before building the Population, follows the authors'
## sample_trajectories.jl (100 gossip-only burn-in rounds, then evolve_modified_loop! until one strategy has fixed),
## and writes one JSON line to ~/simulation_results/kawakatsu2024_gossip/runs/stage<k>/<seed>.json.

using Distributed

const AUTHORS = joinpath(homedir(), "simulation_results", "kawakatsu2024_gossip", "NeutralGossip")
const RUNS = joinpath(homedir(), "simulation_results", "kawakatsu2024_gossip", "runs")
const AUTHORS_COMMIT = "9d894a79a63f5276817ec2ca3c82a39d107fc376"
const N = 100
const B, C = 5.0, 1.0
const UA, UE = 0.02, 0.02
const OMEGA, MU = 1.0, 0.0
const BURN = 100
const CAP = 200_000
const REPS = 50
const WORKERS = 28
const ATTEMPT = Dict(1 => 1, 2 => 1, 3 => 1)   # raised only for the one documented technical repair per stage
const SJ = [1 0; 0 1]           # authors' SJ_norm: [view of recipient + 1, action + 1]
const SS = [1 1; 0 1]           # authors' SS_norm
const STARTS = [(0.6, 0.3, 0.1), (0.4, 0.4, 0.2), (0.2, 0.5, 0.3),
                (0.6, 0.1, 0.3), (0.4, 0.2, 0.4), (0.2, 0.3, 0.5)]          # (ALLC, ALLD, DISC)
const STAGES = Dict(
    1 => (norm = "SJ", starts = 1:6, taus = [0.0, 0.4]),
    2 => (norm = "SJ", starts = [6], taus = [0.05, 0.10, 0.15, 0.20, 0.30]),
    3 => (norm = "SS", starts = 1:6, taus = [0.0, 0.4]),
)

seed_for(stage, start, tau_index, rep) = 100_000 * stage + 1_000 * start + 100 * tau_index + rep
gossip_events(tau_paper) = floor(Int64, (tau_paper / 2) * N^3)   # paper τ: T = τ N³ / 2; code: glen = τ_code N³

function manifest(stage)
    st = STAGES[stage]
    [(stage = stage, norm = st.norm, start = s, tau = t, tau_index = ti - 1, rep = r,
      seed = seed_for(stage, s, ti - 1, r)) for s in st.starts for (ti, t) in enumerate(st.taus) for r in 1:REPS]
end

@everywhere using Random, Statistics
@everywhere include(joinpath(homedir(), "simulation_results", "kawakatsu2024_gossip", "NeutralGossip", "NeutralGossip.jl"))
@everywhere using .NeutralGossip

@everywhere begin

    jval(x::AbstractString) = "\"" * x * "\""
    jval(x::Real) = isfinite(x) ? string(x) : "null"
    jval(x::AbstractVector) = "[" * join(jval.(x), ",") * "]"
    to_json(d) = "{" * join(["\"$(k)\":" * jval(v) for (k, v) in sort(collect(d); by = first)], ",") * "}\n"

    const _ALLD, _ALLC, _DISC = BitVector([0, 0]), BitVector([1, 1]), BitVector([0, 1])

    # counts in the order ALLC, ALLD, DISC (the module's own order is ALLD, ALLC, DISC)
    counts_cad(pop) = (count(r -> r == _ALLC, eachrow(pop.strategies)), count(r -> r == _ALLD, eachrow(pop.strategies)),
                       count(r -> r == _DISC, eachrow(pop.strategies)))

    function setup(n, start, norm, glen; b = 5.0, c = 1.0, ua = 0.02, ue = 0.02, omega = 1.0, mu = 0.0)
        sp = SimParams(n, b, c, ua, ue, omega, mu, BitMatrix(norm))
        pop = Population(n)
        n_allc = floor(Int64, n * start[1])
        n_alld = floor(Int64, n * start[2])
        for i in 1:n_allc
            pop.strategies[i, :] = [1, 1]
        end
        for i in (n_allc + 1):(n_allc + n_alld)
            pop.strategies[i, :] = [0, 0]
        end
        return sp, pop, GossipParams(glen)
    end

    # outcome from counts in the order ALLC, ALLD, DISC
    classify(cc, n) = cc[1] == n ? "ALLC" : cc[2] == n ? "ALLD" : cc[3] == n ? "DISC" : "censored"

    function one_run(job, n, burn, cap, glen, norm, b, c, ua, ue, omega, mu, outdir)
        path = joinpath(outdir, "$(job.seed).json")
        isfile(path) && error("record $path exists; refusing to overwrite")
        Random.seed!(job.seed)                       # before Population(): it draws random views and actions
        sp, pop, gp = setup(n, job.startvec, norm, glen; b = b, c = c, ua = ua, ue = ue, omega = omega, mu = mu)
        c0 = counts_cad(pop)
        for _ in 1:burn
            do_gossip!(pop, sp, gp)
        end
        gens = 0
        coop_sum = 0.0
        alld_extinct = c0[2] == 0 ? 0 : -1
        fixed = classify(c0, n) != "censored"
        while !fixed && gens < cap
            evolve_modified_loop!(pop, sp, gp)
            gens += 1
            coop_sum += sum(pop.actions) / n^2           # all N² simulated pairs, as the module's mean(pop.actions)
            cc = counts_cad(pop)
            if alld_extinct < 0 && cc[2] == 0
                alld_extinct = gens
            end
            fixed = classify(cc, n) != "censored"
        end
        cc = counts_cad(pop)
        rec = Dict(:stage => job.stage, :norm => job.norm, :start => job.start, :tau => job.tau, :rep => job.rep,
                   :seed => job.seed, :gossip_events => gp.tau, :initial_ALLC_ALLD_DISC => collect(c0),
                   :final_ALLC_ALLD_DISC => collect(cc), :outcome => classify(cc, n), :generations => gens,
                   :coop_rate_mean => gens > 0 ? coop_sum / gens : NaN, :alld_extinct_generation => alld_extinct)
        tmp = path * ".tmp.$(getpid())"
        open(tmp, "w") do io
            print(io, to_json(rec))
        end
        isfile(path) && error("record $path appeared during the run; refusing to overwrite")
        mv(tmp, path)
        return rec
    end
end

function preflight()
    # 1. gossip scaling, and the count actually passed to the module
    @assert gossip_events(0.4) == floor(Int64, 0.2 * N^3) == 200_000
    @assert gossip_events(0.0) == 0
    for t in (0.0, 0.05, 0.4)
        _, _, gp = setup(N, STARTS[1], SJ, gossip_events(t))
        @assert gp.tau == gossip_events(t)
    end
    # 2. gossip execution: do_gossip! with G events equals G hand-applied triplets from the same stream,
    #    and leaves the stream at the same point (so exactly 3G draws were made)
    for g in (0, 1, 1000)
        Random.seed!(77)
        sp, pop, gp = setup(N, STARTS[1], SJ, g)
        do_gossip!(pop, sp, gp)
        after = rand()
        Random.seed!(77)
        _, ref, _ = setup(N, STARTS[1], SJ, g)
        v0 = copy(ref.views)
        for _ in 1:g
            i, j, k = rand(1:N, 3)
            ref.views[i, k] = ref.views[j, k]
        end
        @assert pop.views == ref.views && rand() == after "gossip execution, G = $g"
        g == 0 && @assert pop.views == v0
        g == 1000 && @assert pop.views != v0
    end
    # 3. norm indexing: with uniform views v and actions a and no errors, every new view is norm[v + 1, a + 1]
    for (name, norm) in (("SJ", SJ), ("SS", SS)), v in (0, 1), a in (0, 1)
        sp = SimParams(5, 5.0, 1.0, 0.0, 0.0, 1.0, 0.0, BitMatrix(norm))
        pop = Population(5)
        pop.views .= Bool(v)
        pop.actions .= Bool(a)
        NeutralGossip.update_views!(pop, sp)
        @assert all(pop.views .== Bool(norm[v + 1, a + 1])) "norm $name view $v action $a"
    end
    # stern judging: defect against bad = good, cooperate with bad = bad; simple standing: only defect-vs-good bad
    @assert SJ[1, 1] == 1 && SJ[1, 2] == 0 && SJ[2, 1] == 0 && SJ[2, 2] == 1
    @assert SS[1, 1] == 1 && SS[1, 2] == 1 && SS[2, 1] == 0 && SS[2, 2] == 1
    # 4. strategy order and initial counts
    for s in STARTS
        sp, pop, _ = setup(N, s, SJ, 0)
        cad = counts_cad(pop)
        @assert cad == (round(Int, N * s[1]), round(Int, N * s[2]), round(Int, N * s[3])) "start $s gives $cad"
        f = get_frequencies(pop, sp)                 # module order: ALLD, ALLC, DISC
        @assert (round(Int, f[1] * N), round(Int, f[2] * N), round(Int, f[3] * N)) == (cad[2], cad[1], cad[3])
    end
    # 5. payoffs against a hand computation: 3 individuals, 1 cooperates with 2 and 3, 2 cooperates with 1 only
    sp = SimParams(3, 5.0, 1.0, 0.0, 0.0, 1.0, 0.0, BitMatrix(SJ))
    pop = Population(3)
    pop.actions .= false
    pop.actions[1, 2] = true; pop.actions[1, 3] = true; pop.actions[2, 1] = true
    NeutralGossip.update_fitnesses!(pop, sp)
    @assert pop.fitnesses ≈ [(5 * 1 - 1 * 2) / 3, (5 * 1 - 1 * 1) / 3, (5 * 1 - 0) / 3]
    # 6. fixation classification, each strategy and mixed populations
    for (s, want) in (((1.0, 0.0, 0.0), "ALLC"), ((0.0, 1.0, 0.0), "ALLD"), ((0.0, 0.0, 1.0), "DISC"),
                      ((0.99, 0.01, 0.0), "censored"), ((0.0, 0.01, 0.99), "censored"), (STARTS[6], "censored"))
        _, pop, _ = setup(N, s, SJ, 0)
        @assert classify(counts_cad(pop), N) == want "classify $s"
    end
    # 7. seed manifest unique and stage sizes as registered
    for (k, n) in ((1, 600), (2, 250), (3, 600))
        m = manifest(k)
        @assert length(m) == n && length(unique(j.seed for j in m)) == n
    end
    allseeds = [j.seed for k in 1:3 for j in manifest(k)]
    @assert length(unique(allseeds)) == length(allseeds)
    # 8. the authors' code is at the registered commit and unmodified
    head = strip(read(`git -C $AUTHORS rev-parse HEAD`, String))
    @assert head == AUTHORS_COMMIT "authors' code at $head"
    dirty = strip(read(`git -C $AUTHORS status --porcelain --untracked-files=no`, String))
    @assert isempty(dirty) "authors' code modified"
    return true
end

# Stage 2 and 3 run only if analyze.py wrote a Stage 1 verdict that meets the criteria
function stage1_met()
    f = joinpath(RUNS, "stage1", "attempt$(ATTEMPT[1])", "verdict.json")
    isfile(f) || return false
    occursin("\"stage1_met\": true", read(f, String))
end

function provenance()
    here = @__DIR__
    rev = strip(read(`git -C $here rev-parse HEAD`, String))
    for f in ("run_check.jl", "run_stage1.jl", "run_stage2.jl", "run_stage3.jl", "preflight.jl", "analyze.py",
              "PREREGISTRATION.md")
        success(`git -C $here ls-files --error-unmatch $f`) || error("$f is not tracked; commit it before a registered stage")
    end
    dirty = strip(read(`git -C $here status --porcelain --untracked-files=all -- .`, String))
    isempty(dirty) || error("driver directory has uncommitted changes; commit before a registered stage:\n$dirty")
    man = joinpath(Base.active_project() |> dirname, "Manifest.toml")
    mhash = strip(read(`sha256sum $man`, String))
    return "time $(now_string())\ndriver_commit $rev\njulia $(VERSION)\nmanifest $mhash\nauthors_commit $AUTHORS_COMMIT\n" *
           "workers $(nworkers())\n"
end

function run_stage(stage)
    preflight()
    st = STAGES[stage]
    jobs = [merge(j, (startvec = STARTS[j.start], glen = gossip_events(j.tau))) for j in manifest(stage)]
    nw = min(WORKERS, length(jobs))
    nworkers() < nw && error("start Julia with -p $nw (see run_stage$stage.jl)")
    stage > 1 && !stage1_met() && error("stage $stage needs a Stage 1 verdict meeting the criteria (analyze.py)")
    prov = provenance()
    outdir = joinpath(RUNS, "stage$stage", "attempt$(ATTEMPT[stage])")
    mkpath(dirname(outdir))
    mkdir(outdir)                                # atomic claim: fails if this attempt was already started
    write(joinpath(outdir, "provenance.txt"), prov)
    norm = st.norm == "SJ" ? SJ : SS
    t0 = time()
    recs = run_jobs(jobs, norm, CAP, outdir)
    write(joinpath(outdir, "complete.txt"), "$(length(recs)) runs in $(round(time() - t0, digits = 1)) s, $(now_string())\n")
    println("stage $stage: $(length(recs)) runs in $(round(time() - t0, digits = 1)) s")
    return recs
end

# master-only constants are copied into locals so the closure sent to the workers carries their values
function run_jobs(jobs, norm, cap, outdir)
    n, burn, b, c, ua, ue, omega, mu = N, BURN, B, C, UA, UE, OMEGA, MU
    pmap(j -> one_run(j, n, burn, cap, j.glen, norm, b, c, ua, ue, omega, mu, outdir), jobs)
end

now_string() = string(Base.Libc.strftime("%Y-%m-%d %H:%M:%S", time()))
