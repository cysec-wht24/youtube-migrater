import json
from collections import defaultdict

# Load JSON dictionary
with open("data/parsed_activity.json", "r") as f:
    data = json.load(f)

def duplicates_with_indices(d):
    """
    For each key in the dictionary whose value is a list,
    find duplicates and return their indices.
    """
    result = {}
    
    for key, values in d.items():
        value_indices = defaultdict(list)
        
        # Collect indices for each value
        for idx, val in enumerate(values):
            value_indices[val].append(idx)
        
        # Filter only values that appear more than once
        duplicates = {val: idxs for val, idxs in value_indices.items() if len(idxs) > 1}
        
        if duplicates:
            result[key] = duplicates
    
    return result

# Run the function
dup_result = duplicates_with_indices(data)

print("Duplicates with positions:")
for key, dup_info in dup_result.items():
    print(f"\nKey: {key}")
    total_dupes = 0
    for val, idxs in dup_info.items():
        print(f"  Value {val} occurs at indices {idxs}")
        total_dupes += len(idxs)
    print(f"  Total duplicate entries for key '{key}': {total_dupes}")
