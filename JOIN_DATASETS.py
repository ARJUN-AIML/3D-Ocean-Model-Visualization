import os

DATASETS_TO_JOIN = [
    {
        "target": "RSMC_hycom_20260904.nc",
        "folder": "hycom",
        "prefix": "RSMC_hycom_20260904.nc.part"
    },
    {
        "target": "rsmc_combined_ww3_20260903.nc",
        "folder": "combined",
        "prefix": "rsmc_combined_ww3_20260903.nc.part"
    }
]

def join_dataset(item):
    target_path = item["target"]
    folder = item["folder"]
    prefix = item["prefix"]
    
    if os.path.exists(target_path):
        print(f"Target file '{target_path}' already exists. Skipping join.")
        return

    print(f"\n--- Joining parts from '{folder}' into '{target_path}' ---")
    part_num = 1
    parts = []
    
    while True:
        part_name = os.path.join(folder, f"{prefix}{part_num}")
        if os.path.exists(part_name):
            parts.append(part_name)
            part_num += 1
        else:
            break
            
    if not parts:
        print(f"No parts found in '{folder}/' for {target_path}.")
        return

    print(f"Found {len(parts)} parts in '{folder}/'. Recombining...")
    with open(target_path, 'wb') as f_out:
        for p in parts:
            print(f"  Appending {p}...")
            with open(p, 'rb') as f_in:
                while True:
                    chunk = f_in.read(64 * 1024 * 1024)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    
    print(f"Successfully reconstructed '{target_path}' ({os.path.getsize(target_path) / (1024**3):.2f} GB)")

if __name__ == "__main__":
    for item in DATASETS_TO_JOIN:
        join_dataset(item)
