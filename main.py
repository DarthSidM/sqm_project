import os
import sys
from collections import defaultdict

# Import the metric calculations from our new modules
import argparse
import json

from common import get_js_files, extract_tokens, classify_tokens
from halstead import halstead_metrics
from information_flow import compute_fan_in_out
from live_variables import compute_live_vars
from size_metrics import compute_size_metrics
from oo_metrics import compute_oo_metrics
from testing_metrics import compute_testing_metrics

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

    all_files = []
    for d in directories:
        files = get_js_files(d)
        if not files:
            print(f"ℹ No source files found in {d}")
            continue
        all_files.extend(files)

    if not all_files:
        print("ℹ No source files found in any provided directory")
        return None

    for file in all_files:
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

                # 2.5 Size metrics (per-file aggregation)
                sres = compute_size_metrics(code)
                if sres:
                    total_loc += sres.get('LOC', 0)
                    total_sloc += sres.get('SLOC', 0)
                    total_comments += sres.get('CommentLines', 0)
                    total_blank += sres.get('BlankLines', 0)
                    total_avg_line_length += sres.get('AvgLineLength', 0)

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

    # 2.5 Size metrics aggregated
    avg_line_length = (total_avg_line_length / max(1, file_count))
    size_results = {
        'TotalLOC': total_loc,
        'TotalSLOC': total_sloc,
        'TotalCommentLines': total_comments,
        'TotalBlankLines': total_blank,
        'AvgLineLength': avg_line_length,
    }

    # 3. Live Variables Metrics
    avg_live_vars_per_file = total_avg_live_metric / max(1, file_count)
    live_vars_results = {
        "TotalLiveVariables": total_live_vars,
        "AvgLiveVariablesPerFile": avg_live_vars_per_file,
    }

    # 4. OO metrics: aggregate across files by combining per-file detections
    total_classes = 0
    total_methods = 0
    max_inheritance_depth = 0
    for file in all_files:
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            oores = compute_oo_metrics(code)
            if oores:
                total_classes += int(oores.get('TotalClasses', 0))
                total_methods += int(oores.get('TotalMethods', 0))
                d = int(oores.get('MaxInheritanceDepth', 0))
                if d > max_inheritance_depth:
                    max_inheritance_depth = d
        except Exception:
            continue

    avg_methods_per_class = (total_methods / total_classes) if total_classes > 0 else 0
    oo_results = {
        'TotalClasses': total_classes,
        'TotalMethods': total_methods,
        'AvgMethodsPerClass': avg_methods_per_class,
        'MaxInheritanceDepth': max_inheritance_depth,
    }

    # 5. Testing metrics (file-list based)
    test_metrics = compute_testing_metrics(all_files)

    # Return all metrics structured separately
    return {
        "halstead": halstead_results,
        "info_flow": info_flow_results,
        "live_vars": live_vars_results,
        "size": size_results,
        "oo": oo_results,
        "testing": test_metrics,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compute code metrics for JS/TS projects')
    parser.add_argument('dirs', nargs='*', help='Root directories to analyze', default=["./frontend/src", "./backend"])
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    args = parser.parse_args()

    # Validate directories exist
    root_dirs = args.dirs if args.dirs else ["./frontend/src", "./backend"]
    valid_dirs = [d for d in root_dirs if os.path.isdir(d)]

    if not valid_dirs:
        print(f"❌ Error: None of the specified directories exist: {root_dirs}")
        print("Please supply valid source directories, e.g.\n  ./main.py ./frontend/src ./backend")
        sys.exit(2)

    print(f"🔍 Analyzing project for metrics in: {valid_dirs}\n")
    all_metrics = analyze_project(valid_dirs)

    if not all_metrics:
        print("⚠ Analysis finished, but no metrics were calculated.")
        sys.exit(0)

    if args.json:
        print(json.dumps(all_metrics, indent=2))
        sys.exit(0)

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
    print_metric_group("Size Metrics", all_metrics.get("size"))
    print_metric_group("Object-Oriented Metrics", all_metrics.get("oo"))
    print_metric_group("Testing Metrics", all_metrics.get("testing"))