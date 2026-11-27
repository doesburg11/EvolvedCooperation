## Preflight checks of PREREGISTRATION.md (no outcome is read). Launch: julia --project=$HOME/simulation_results/kawakatsu2024_gossip preflight.jl
include(joinpath(@__DIR__, "run_check.jl"))
preflight() && println("preflight: all checks passed")
