## Stage 1 of PREREGISTRATION.md. Launch: julia --project=$HOME/simulation_results/kawakatsu2024_gossip -p 28 run_stage1.jl
include(joinpath(@__DIR__, "run_check.jl"))
run_stage(1)
