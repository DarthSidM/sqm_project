import os
import sys
from collections import defaultdict

# Import the metric calculations from our new modules
from common import get_js_files, extract_tokens, classify_tokens
from halstead import halstead_metrics
from information_flow import compute_fan_in_out
from live_variables import compute_live_vars

def analyze_project(directories):
    """
    Analyzes all files in the given directories and aggregates metrics.
    """
    all_ops, all_oprs = [], []
    total_live_vars = 0
    total_avg_live_metric = 0
    info_flow_values = []
    fan_in_values = []
    fan_out_values = []
    file_count = 0

    for d in directories:
        files = get_js_files(d)
        if not files:
            print(f"ℹ No source files found in {d}")
            continue
            
        for file in files:
            file_count += 1
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                # 1. Halstead (token-based, aggregated)
                tokens = extract_tokens(file)
                ops, oprs = classify_tokens(tokens)
                all_ops.extend(ops)
                all_oprs.extend(oprs)

                # 2. Live variable metrics (code-based, aggregated)
                lv, avg_lv = compute_live_vars(code)
                total_live_vars += lv
                total_avg_live_metric += avg_lv

                # 3. Henry–Kafura info (code-based, aggregated)
                # compute_fan_in_out now returns a mapping function_name ->
                # { 'fan_in': int, 'fan_out': int, 'information_flow': int }
                info_flow = compute_fan_in_out(code)
                if info_flow:
                    # extract numeric information_flow, fan_in and fan_out values for averaging
                    for v in info_flow.values():
                        if isinstance(v, dict):
                            if 'information_flow' in v:
                                try:
                                    info_flow_values.append(float(v['information_flow']))
                                except Exception:
                                    pass
                            if 'fan_in' in v:
                                try:
                                    fan_in_values.append(float(v['fan_in']))
                                except Exception:
                                    pass
                            if 'fan_out' in v:
                                try:
                                    fan_out_values.append(float(v['fan_out']))
                                except Exception:
                                    pass
                        elif isinstance(v, (int, float)):
                            info_flow_values.append(float(v))
            
            except Exception as e:
                print(f"⚠ Could not analyze {file}: {e}")

    if file_count == 0:
        print("⚠ No valid files found to analyze.")
        return None

    # --- Aggregate Metrics ---

    # 1. Halstead Metrics
    halstead_results = halstead_metrics(all_ops, all_oprs)
    if not halstead_results:
        return None

    # 2. Information Flow Metrics
    avg_info_flow = sum(info_flow_values) / max(1, len(info_flow_values))
    total_fan_in = sum(fan_in_values)
    total_fan_out = sum(fan_out_values)
    avg_fan_in = total_fan_in / max(1, len(fan_in_values))
    avg_fan_out = total_fan_out / max(1, len(fan_out_values))

    info_flow_results = {
        "AvgInformationFlow": avg_info_flow,
        "TotalFanIn": total_fan_in,
        "TotalFanOut": total_fan_out,
        "AvgFanIn": avg_fan_in,
        "AvgFanOut": avg_fan_out,
    }

    # 3. Live Variables Metrics
    avg_live_vars_per_file = total_avg_live_metric / max(1, file_count)
    live_vars_results = {
        "TotalLiveVariables": total_live_vars,
        "AvgLiveVariablesPerFile": avg_live_vars_per_file,
    }

    # Return all metrics structured separately
    return {
        "halstead": halstead_results,
        "info_flow": info_flow_results,
        "live_vars": live_vars_results
    }


if __name__ == "__main__":
    # Accept directories from command-line arguments if provided,
    # otherwise fall back to sensible defaults.
    if len(sys.argv) > 1:
        root_dirs = sys.argv[1:]
    else:
        # --- IMPORTANT ---
        # Default directories (can be overridden via CLI):
        root_dirs = ["./frontend/src", "./backend"]

    # Validate directories exist
    valid_dirs = [d for d in root_dirs if os.path.isdir(d)]

    if not valid_dirs:
        print(f"❌ Error: None of the specified directories exist: {root_dirs}")
        print("Please supply valid source directories, e.g.:\n  radonhal ./frontend/src ./backend")
    else:
        print(f"🔍 Analyzing project for metrics in: {valid_dirs}\n")
        all_metrics = analyze_project(valid_dirs)
        
        if all_metrics:
            
            # Helper function for printing
            def print_metric_group(title, metrics_dict):
                print(f"📊 {title}\n" + "-" * (len(title) + 3))
                if not metrics_dict:
                    print("   (No data)\n")
                    return
                for k, v in metrics_dict.items():
                    print(f"   {k:25s}: {v:.2f}" if isinstance(v, float) else f"   {k:25s}: {v}")
                print("\n" + "-" * 30 + "\n") # Separator

            # Print each group separately
            print_metric_group("Halstead Complexity Metrics", all_metrics.get("halstead"))
            print_metric_group("Information Flow Metrics", all_metrics.get("info_flow"))
            print_metric_group("Live Variable Metrics", all_metrics.get("live_vars"))
            
        else:
            print("⚠ Analysis finished, but no metrics were calculated.")